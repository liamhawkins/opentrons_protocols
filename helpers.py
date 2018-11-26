# COPY AND PASTE INTO EACH PROTOCOL FILE
class TipTracker:
    # TODO: Support multiple tip_racks
    # TODO: Support returning tips
    """
    TipTracker tracks the tips used by an 8-channel pipette so it can be used as a single channel. TipTracker.next_tip()
    take n tips as an argument and return location of a tiprack that would result in the pipette picking up that many
    tips
    """
    def __init__(self, tiprack):
        self.tiprack = tiprack
        self.letters = list(reversed(list('ABCDEFGH')))
        self.nums = list(range(1, 12 + 1))
        self.num_rows = len(self.letters)
        self.num_cols = len(self.nums)
        self.rack = []

        # Creates tip layout as nested list of lists
        for n in self.nums:
            col = []
            for l in self.letters:
                col.append('{}{}'.format(l, n))
            self.rack.append(col)

    def __str__(self):
        for i in range(self.num_rows):
            row = []
            for col in self.rack:
                row.append(col[-i-1])
            print(row)

    def next_tip(self, n=1):
        """
        Returns location on tiprack that would result in pipette picking up n tips when passed as location parameter to
        Pipette.pick_up_tip()

        Parameters
        ----------
        n: int
            Number of tips to pick up

        Returns
        -------
        location
            Location on tiprack that would result in pipette picking up n tips
        """
        assert n <= 8, "Cannot pick up more than 8 tips"
        for i in range(self.num_cols):
            for j in list(range(self.num_rows)):
                # Scan up columns until n non-empty tips are found
                try:
                    self.rack[i][j+n-1]
                except IndexError:
                    continue
                tips = self.rack[i][j:j+n]
                # If any tips are empty (None) continue scanning up column or next column
                if any(x is None for x in tips):
                    continue
                else:
                    # When usable tips are found, set them to None and return highest tip in the column
                    for t in range(n):
                        self.rack[i][j+t] = None
                    tip_name = tips[-1]
                    print("\nTaking {} tips".format(n))
                    return self.tiprack.wells(tip_name)


def multiwell_location_offset(plates, x=0, y=0, z=0, start_column=None, end_column=None, columns=None):
    from opentrons.legacy_api.containers.placeable import Container
    if isinstance(plates, Container):
        plates = list(plates)
    if columns is not None:
        return [(col[0], col[0].from_center(x=x, y=y, z=z)) for plate in plates for col in plate.columns(columns)]
    elif start_column and end_column:
        return [(col[0], col[0].from_center(x=x, y=y, z=z)) for plate in plates for col in plate.columns(start_column, to=end_column)]


