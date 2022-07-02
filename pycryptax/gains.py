import copy, datetime
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

class AggregateDayTxs:

    def __init__(self):

        self.acquireAmt = 0
        self.acquireVal = 0

        self.disposeAmt = 0
        self.disposeVal = 0

    def acquire(self, amt, val):
        self.acquireAmt += amt
        self.acquireVal += val

    def dispose(self, amt, val):
        self.disposeAmt += amt
        self.disposeVal += val

    def __repr__(self):
        return 'acquireAmt={}, acquireVal={}; disposeAmt={}, disposeVal={}'.format(
            self.acquireAmt,
            self.acquireVal,
            self.disposeAmt,
            self.disposeVal,
        )

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

class Rule(Enum):
    SAME_DAY = "SAME DAY"
    BED_AND_BREAKFASTING = "BED AND BREAKFASTING"

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

        # Obtain total acquisition and disposal values for each day for every
        # asset

        assetTxs = {}

        def getDayTxForAsset(asset, date):

            if asset not in assetTxs:
                assetTxs[asset] = datemap.DateMap()

            dayTxs = assetTxs[asset]

            if date not in dayTxs:
                return dayTxs.insert(date, AggregateDayTxs())

            return dayTxs[date]

        for date, tx in gainData:
            if tx.amount > 0:
                # Acquisition

                getDayTxForAsset(tx.asset, date).acquire(
                    tx.amount,
                    tx.amount * tx.price + tx.fee
                )

            if tx.amount < 0:
                # Disposal

                amount = abs(tx.amount)
                getDayTxForAsset(tx.asset, date).dispose(
                    amount,
                    amount * tx.price - tx.fee
                )

        def applyGain(asset, gain, date):

            if date < start or date > end:
                return False

            if self._includeSummary:
                self._totalGain += gain
                util.addToDictKey(self._assetGain, asset, gain)

            if self._includeDisposals:
                self._disposals.insert(date, (asset, gain))

            return True

        def gainOrLoss(profit):
            if profit >= Decimal(0.01):
                return "GAIN"
            elif profit <= Decimal(-0.01):
                return "LOSS"
            else:
                return "neither GAIN nor LOSS"

        def match(
                asset: str,
                date: datetime.datetime,
                matchDate: datetime.datetime,
                disposeTx: AggregateDayTxs,
                acquireTx: AggregateDayTxs,
                rule: Rule,
        ):

            # Get amount that can be matched
            amount = min(disposeTx.disposeAmt, acquireTx.acquireAmt)

            if amount == 0:
                # Cannot match nothing
                return

            # Get proportion of cost
            cost = Decimal(acquireTx.acquireVal * amount / acquireTx.acquireAmt)

            # Get proportion of disposal value
            value = Decimal(disposeTx.disposeVal * amount / disposeTx.disposeAmt)

            # Apply gain/loss
            reportable = applyGain(asset, Gain(cost, value), date)

            # Adjust data to remove amounts and report asset values that have
            # been accounted for

            disposeValue = disposeTx.disposeVal

            disposeTx.disposeAmt -= amount
            acquireTx.acquireAmt -= amount

            disposeTx.disposeVal -= value
            acquireTx.acquireVal -= cost

            if reportable:
                self.total_number_of_disposals += 1
                profit = value - cost
                print("{id}. SELL: {amount} {asset} on {dt} at £{disposePrice:.04f} (including fees) "
                      "gives {gain_or_loss} of £{profit:.02f}".format(
                    id=self.total_number_of_disposals,
                    amount=amount,
                    asset=asset,
                    dt=date.strftime("%d/%m/%Y"),
                    gain_or_loss=gainOrLoss(profit),
                    disposePrice=value / amount,
                    profit=abs(profit),
                ))
                print("Matches with:\n"
                      "BUY: {amount} {asset} shares bought on {dt} at £{price:0.4f} (including fees) according to {rule} rule\n\n".format(
                    asset=asset,
                    amount=amount,
                    dt=matchDate.strftime("%d/%m/%Y"),
                    price=cost / amount,
                    rule=rule.value,
                ))

        for asset, dayTxs in assetTxs.items():

            # Same-day rule: Match disposals to acquisitions that happen on the same day

            for date, tx in dayTxs:
                match(asset, date, date, tx, tx, Rule.SAME_DAY)

            # Bed and breakfasting rule
            # Match disposals to nearest acquisitions from 1->30 days afterwards

            for date, tx in dayTxs:

                # Only process disposals
                if tx.disposeAmt == 0:
                    continue

                # Loop though transactions in range to match against
                for matchDate, matchTx in dayTxs.range(
                    date + datetime.timedelta(days=1),
                    date + datetime.timedelta(days=30)
                ):
                    match(asset, date, matchDate, tx, matchTx, Rule.BED_AND_BREAKFASTING)

            # Process section 104 holdings from very beginning but only count gains
            # realised between start and end.

            for date, tx in dayTxs:

                # Only an acquisition or disposal, not both allowed.
                # Should have been previously matched
                assert(not (tx.acquireAmt != 0 and tx.disposeAmt != 0))

                if tx.acquireAmt != 0:

                    # Adjust section 104 holding

                    if asset not in self._assetPools:
                        self._assetPools[asset] = AssetPool()

                    self._assetPools[asset].add(tx.acquireAmt, tx.acquireVal)

                if tx.disposeAmt != 0:

                    if asset not in self._assetPools:
                        raise ValueError("Disposing of an asset ({}) not acquired: {}".format(asset, tx))

                    average_price = 0

                    # Adjust section 104 holding and get cost
                    try:
                        total_cost = self._assetPools[asset].totalCost
                        total_amount = self._assetPools[asset].totalQuantity
                        average_price = total_cost / total_amount
                        cost = self._assetPools[asset].dispose(tx.disposeAmt)
                    except ValueError as e:
                        print(util.getPrettyDate(date) + " (" + asset + "): " + str(e))
                        raise e

                    # Apply gain/loss
                    reportable = applyGain(asset, Gain(cost, tx.disposeVal), date)
                    if reportable:
                        self.total_number_of_disposals += 1
                        profit = tx.disposeVal - cost
                        print("{id}. SELL: {amount} {asset} on {dt} at £{price:.04f} (including fees) "
                              "gives {gain_or_loss} of £{profit:.02f}".format(
                            id=self.total_number_of_disposals,
                            amount=tx.disposeAmt,
                            asset=asset,
                            dt=date.strftime("%d/%m/%Y"),
                            gain_or_loss=gainOrLoss(profit),
                            price=tx.disposeVal / tx.disposeAmt,
                            profit=abs(profit),
                        ))
                        print("Matches with:\nBUY: SECTION 104 HOLDING. {amount} {asset} shares of {total_amount} "
                              "bought at average price of £{average_price:.04f} (including fees)\n\n".format(
                            asset=asset,
                            amount=tx.disposeAmt,
                            total_amount=total_amount,
                            average_price=average_price,
                        ))

                if date <= end:
                    # Update asset pools up until the end of the range to get the
                    # section 104 holdings at the point of the end of the range
                    self._assetPoolsAtEnd[asset] = copy.deepcopy(self._assetPools[asset])

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
