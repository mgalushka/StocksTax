import copy, datetime
import logging
from decimal import Decimal
from enum import Enum

from pycryptax import util, output, datemap
from pycryptax.csvdata import CSVTransactionGains


class AssetPool:

    def __init__(self):
        self.totalQuantity = 0
        self.totalCost = 0

    def add(self, quantity, cost):
        self.totalQuantity += quantity
        self.totalCost += cost

    def dispose(self, quantity):

        if quantity > self.totalQuantity:
            raise ValueError(
                "Quantity of asset being disposed, is more than existing. {} > {}"
                .format(quantity, self.totalQuantity)
            )

        cost = self.totalCost * quantity / self.totalQuantity
        self.totalQuantity -= quantity
        self.totalCost -= cost

        return cost

    def __repr__(self):
        return "AssetPool({}, {})".format(self.totalQuantity, self.totalCost)

class Gain:

    def __init__(self, cost: Decimal = Decimal(0), value: Decimal = Decimal(0)):
        self._value = value
        self._cost = cost

    def __iadd__(self, b):
        self._value += b._value
        self._cost += b._cost
        return self

    def cost(self):
        return self._cost

    def value(self):
        return self._value

    def gain(self):
        return self._value - self._cost

    def __str__(self):
        return '[Value={},Cost={},Gain={}]'.format(self.value(), self.cost(), self.gain())

class Rule(Enum):
    SAME_DAY = "SAME DAY"
    BED_AND_BREAKFASTING = "BED AND BREAKFASTING"

class _Acquisition:

    def __init__(self, date, amount, cost):
        self.date = date
        self.remaining = amount
        self.remaining_cost = cost

class _Disposal:

    def __init__(self, date, amount, value, index):
        self.date = date
        self.amount = amount
        self.value = value
        self.index = index
        self.remaining = amount
        self.remaining_value = value
        self.matches = []

class _Match:

    def __init__(self, amount, cost, rule=None, match_date=None, price=None,
                 total_amount=None, average_price=None):
        self.amount = amount
        self.cost = cost
        self.rule = rule
        self.match_date = match_date
        self.price = price
        self.total_amount = total_amount
        self.average_price = average_price

class CapitalGainCalculator:

    def __init__(
        self, gainData: CSVTransactionGains, start, end, summary=True, disposals=True,
    ):

        self._start = start
        self._end = end
        self._includeSummary = summary
        self._includeDisposals = disposals

        if summary:
            self._assetGain = {}
            self._totalGain = Gain()

        if disposals:
            self._disposals = datemap.DateMap()

        self._assetPoolsAtEnd = {}
        self._assetPools = {}

        self.total_number_of_disposals = 0

        # Group the individual transactions by asset, keeping them in date
        # order (the CSV data is iterated in date order already).
        assetTxs = {}

        for date, tx in gainData:
            assetTxs.setdefault(tx.asset, []).append((date, tx))

        for asset, txs in assetTxs.items():
            disposals = self._matchAsset(asset, txs)
            self._reportAsset(asset, disposals)

    def _applyGain(self, asset, gain, date):

        logging.debug('Applying gain={} to asset={}, for date={}'.format(gain, asset, date))

        if date < self._start or date > self._end:
            return False

        if self._includeSummary:
            self._totalGain += gain
            util.addToDictKey(self._assetGain, asset, gain)

        if self._includeDisposals:
            self._disposals.insert(date, (asset, gain))

        return True

    @staticmethod
    def _gainOrLoss(profit):
        if profit >= Decimal(0.01):
            return "GAIN"
        elif profit <= Decimal(-0.01):
            return "LOSS"
        else:
            return "neither GAIN nor LOSS"

    def _matchAsset(self, asset, txs):

        acquisitions = []
        disposals = []

        # Same-day acquisitions of the same class are treated as a single
        # asset, so aggregate them. Disposals are kept individual so that each
        # sell transaction is reported separately.
        acquisitions_by_date = {}

        for index, (date, tx) in enumerate(txs):

            if tx.amount > 0:
                # Acquisition: cost is the amount paid plus the fee.
                cost = tx.amount * tx.price + tx.fee

                if date in acquisitions_by_date:
                    acquisitions_by_date[date].remaining += tx.amount
                    acquisitions_by_date[date].remaining_cost += cost
                else:
                    acquisition = _Acquisition(date, tx.amount, cost)
                    acquisitions_by_date[date] = acquisition
                    acquisitions.append(acquisition)

            elif tx.amount < 0:
                # Disposal: value is the proceeds less the fee.
                amount = abs(tx.amount)
                disposals.append(_Disposal(
                    date,
                    amount,
                    amount * tx.price - tx.fee,
                    index,
                ))

        # Apply the HMRC share matching rules in the required order: same-day
        # first, then bed and breakfasting (acquisitions within 30 days), then
        # the Section 104 holding.
        self._matchSameDay(acquisitions, disposals)
        self._matchBedAndBreakfasting(acquisitions, disposals)
        self._matchSection104(asset, acquisitions, disposals)

        return disposals

    def _matchPair(self, disposal, acquisition, rule):

        if disposal.remaining == 0 or acquisition.remaining == 0:
            return

        amount = min(disposal.remaining, acquisition.remaining)

        cost = acquisition.remaining_cost * amount / acquisition.remaining
        value = disposal.remaining_value * amount / disposal.remaining

        disposal.matches.append(_Match(
            amount,
            cost,
            rule=rule,
            match_date=acquisition.date,
            price=cost / amount,
        ))

        acquisition.remaining -= amount
        acquisition.remaining_cost -= cost

        disposal.remaining -= amount
        disposal.remaining_value -= value

    def _matchSameDay(self, acquisitions, disposals):

        acquisitions_by_date = {}

        for acquisition in acquisitions:
            acquisitions_by_date.setdefault(acquisition.date, []).append(acquisition)

        for disposal in disposals:
            for acquisition in acquisitions_by_date.get(disposal.date, ()):

                if disposal.remaining == 0:
                    break

                self._matchPair(disposal, acquisition, Rule.SAME_DAY)

    def _matchBedAndBreakfasting(self, acquisitions, disposals):

        for disposal in disposals:

            if disposal.remaining == 0:
                continue

            for acquisition in acquisitions:

                if acquisition.remaining == 0:
                    continue

                if disposal.date < acquisition.date <= \
                        disposal.date + datetime.timedelta(days=30):
                    self._matchPair(disposal, acquisition, Rule.BED_AND_BREAKFASTING)

                    if disposal.remaining == 0:
                        break

    def _matchSection104(self, asset, acquisitions, disposals):

        if asset not in self._assetPools:
            self._assetPools[asset] = AssetPool()

        pool = self._assetPools[asset]

        # Process the remaining acquisitions and disposals in date order,
        # adding acquisitions to the Section 104 holding and removing
        # disposals from it. After same-day and bed and breakfasting matching
        # a single date never has both a remaining acquisition and a remaining
        # disposal.
        events = [(a.date, a) for a in acquisitions if a.remaining > 0] + \
                 [(d.date, d) for d in disposals if d.remaining > 0]

        events.sort(key=lambda event: event[0])

        for date, event in events:

            if isinstance(event, _Acquisition):

                pool.add(event.remaining, event.remaining_cost)

            else:

                total_amount = pool.totalQuantity
                total_cost = pool.totalCost
                average_price = total_cost / total_amount if total_amount else Decimal(0)

                try:
                    cost = pool.dispose(event.remaining)
                except ValueError as e:
                    print(util.getPrettyDate(date) + " (" + asset + "): " + str(e))
                    raise e

                event.matches.append(_Match(
                    event.remaining,
                    cost,
                    total_amount=total_amount,
                    average_price=average_price,
                ))
                event.remaining = 0

            if date <= self._end:
                # Update asset pools up until the end of the range to get the
                # section 104 holdings at the point of the end of the range
                self._assetPoolsAtEnd[asset] = copy.deepcopy(pool)

    def _reportAsset(self, asset, disposals):

        for disposal in sorted(disposals, key=lambda d: (d.date, d.index)):

            cost = sum((m.cost for m in disposal.matches), Decimal(0))

            reportable = self._applyGain(
                asset, Gain(cost, disposal.value), disposal.date
            )

            if not reportable:
                continue

            self.total_number_of_disposals += 1
            profit = disposal.value - cost

            print("{id}. SELL: {amount} {asset} on {dt} at £{price:.4f} (including fees) "
                  "gives {gain_or_loss} of £{profit:.2f}".format(
                id=self.total_number_of_disposals,
                amount=disposal.amount,
                asset=asset,
                dt=disposal.date.strftime("%d/%m/%Y"),
                gain_or_loss=self._gainOrLoss(profit),
                price=disposal.value / disposal.amount,
                profit=abs(profit),
            ))

            match_lines = []

            for m in disposal.matches:
                if m.rule is not None:
                    match_lines.append(
                        "BUY: {amount} {asset} shares bought on {dt} at £{price:.4f} "
                        "(including fees) according to {rule} rule".format(
                            amount=m.amount,
                            asset=asset,
                            dt=m.match_date.strftime("%d/%m/%Y"),
                            price=m.price,
                            rule=m.rule.value,
                        )
                    )
                else:
                    match_lines.append(
                        "BUY: SECTION 104 HOLDING. {amount} {asset} shares of "
                        "{total_amount} bought at average price of £{average_price:.4f} "
                        "(including fees)".format(
                            amount=m.amount,
                            asset=asset,
                            total_amount=m.total_amount,
                            average_price=m.average_price,
                        )
                    )

            if match_lines:
                print("Matches with:")
                for line in match_lines:
                    print(line)
                print()

    def printSummary(self):

        print("\nTotal number of disposals: {} \n\n".format(self.total_number_of_disposals))

        output.printCalculationTitle("CAPITAL GAIN", self._start, self._end)

        table = output.OutputTable(4)
        table.appendRow("ASSET", "ACQUISITION COST", "DISPOSAL VALUE", "GAIN / LOSS")
        table.appendGap()

        totalGains = Decimal(0)
        totalLosses = Decimal(0)

        for k, v in self._assetGain.items():
            table.appendRow(k, v.cost(), v.value(), v.gain())
            if v.gain() >= 0:
                totalGains += v.gain()
            else:
                totalLosses -= v.gain()

        table.appendGap()
        table.appendRow(
            "TOTAL", self._totalGain.cost(), self._totalGain.value(),
            self._totalGain.gain()
        )

        table.print()

        print("\nYear Gains = £{gains:0.2f}  Year Losses = £{losses:0.2f}".format(
            gains=totalGains,
            losses=totalLosses,
        ))

        return (totalGains, totalLosses)

        # print("SECTION 104 HOLDINGS AS OF {}:\n".format(util.getPrettyDate(self._end)))
        #
        # table = output.OutputTable(5)
        # table.appendRow("ASSET", "AMOUNT", "COST", "VALUE", "UNREALISED GAIN")
        # table.appendGap()
        #
        # totalCost = Decimal(0)
        # totalValue = Decimal(0)

        # for asset, pool in self._assetPoolsAtEnd.items():
        #
        #     value = pool.totalQuantity * 1   # TODO: fix: self._priceData.get(asset, self._end)
        #
        #     totalCost += pool.totalCost
        #     totalValue += value
        #
        #     table.appendRow(
        #         asset, pool.totalQuantity, pool.totalCost, value, value - pool.totalCost
        #     )
        #
        # table.appendGap()
        # table.appendRow("", "TOTAL", totalCost, totalValue, totalValue - totalCost)
        #
        # table.print()
