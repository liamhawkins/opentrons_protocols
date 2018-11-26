from opentrons import labware, instruments


class TipTracker:
    def __init__(self, tiprack=None):
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

    def print_rack(self):
        for i in range(self.num_rows):
            row = []
            for col in self.rack:
                row.append(col[-i-1])
            print(row)

    def next_tip(self, n=1):
        assert n <= 8, "Cannot pick up more than 8 tips"
        for i in range(self.num_cols):
            for j in list(range(self.num_rows)):
                try:
                    self.rack[i][j+n-1]
                except IndexError:
                    continue
                tips = self.rack[i][j:j+n]
                if any(x is None for x in tips):
                    continue
                else:
                    for t in range(n):
                        self.rack[i][j+t] = None
                    tip_name = tips[-1]
                    print("\nTaking {} tips".format(n))
                    return self.tiprack.wells(tip_name)


tube_rack_2ml = labware.load('storeylab-2ml-coldrack1', '7')
tube_rack_15ml = labware.load('opentrons-tuberack-15_50ml', '10')
small_reagent_plate = labware.load('PCR-strip-tall', '8')
pcr_plate1 = labware.load('96-flat', '4')
pcr_plate2 = labware.load('96-flat', '5')
pcr_plate3 = labware.load('96-flat', '6')
tiprack1 = labware.load('opentrons-tiprack-300ul', '11')
tiprack2 = labware.load('opentrons-tiprack-300ul', '9')

tiprack2_tracker = TipTracker(tiprack=tiprack2)

TOTAL_VOL = 20.0
CDNA_VOL = 5.0

WATER_PER_WELL = 12.115 - CDNA_VOL
assert WATER_PER_WELL >= 0, "Water per well is less than 0"
TREH_PER_WELL = 4.0
BUFFER_PER_WELL = 2
FORM_PER_WELL = 0.5
DNTP_PER_WELL = 0.16
SYBR_PER_WELL = 0.1
TAQ_PER_WELL = 0.125
PRIMER_MIX_PER_WELL = 1.0

WELLS = 350
FORMAMIDE_VOL = FORM_PER_WELL*WELLS
DNTP_VOL = DNTP_PER_WELL*WELLS
SYBR_VOL = SYBR_PER_WELL*WELLS
TAQ_VOL = TAQ_PER_WELL*WELLS
MASTER_MIX_TUBE_WELLS = 19.0
MASTER_MIX_TUBE_VOL = (WATER_PER_WELL+TREH_PER_WELL+BUFFER_PER_WELL+FORM_PER_WELL+DNTP_PER_WELL+SYBR_PER_WELL+TAQ_PER_WELL)*MASTER_MIX_TUBE_WELLS
PRIMER_VOL = PRIMER_MIX_PER_WELL * MASTER_MIX_TUBE_WELLS

MASTER_MIX_VOL = TOTAL_VOL-CDNA_VOL


def run_custom_protocol(number_of_mixing: int=10, mix_rate: int=1):
    # LABWARE
    # Define Pipettes
    p300_single = instruments.P300_Single(mount='right', tip_racks=[tiprack1])
    p50_multi = instruments.P50_Multi(mount='left', tip_racks=[tiprack2])

    # Define master mix reagents
    formamide = tube_rack_2ml.wells('A1')
    dntp = small_reagent_plate.wells('A1')
    sybr = small_reagent_plate.wells('B1')
    taq = small_reagent_plate.wells('C1')
    primers = [well.bottom() for well in small_reagent_plate.wells('A3', 'A4', 'A5', 'A6', 'A7', 'A8',
                                                                   'C3', 'C4', 'C5', 'C6', 'C7', 'C8',
                                                                   'E3', 'E4', 'E5', 'E6', 'E7', 'E8')]

    # cDNA
    samples = small_reagent_plate.columns('12')

    # Initial buffer mix in tube (1413.8 uL)
    buffer_mix_tube = tube_rack_15ml.wells('A1')  # Water, Trehalose, qPCR Buffer
    high_vol_buffer_mix_tube = (buffer_mix_tube, buffer_mix_tube.from_center(x=0, y=0, z=-0.25))

    # Separate master mix tubes for each primer
    master_mix_tubes = [well.bottom() for well in tube_rack_2ml.wells('A3', 'A4', 'A5',
                                                                      'B1', 'B2', 'B3', 'B4', 'B5',
                                                                      'C1', 'C2', 'C3', 'C4', 'C5',
                                                                      'D1', 'D2', 'D3', 'D4', 'D5')]

    # PROTOCOL
    # Make master mix
    p300_single.distribute(FORMAMIDE_VOL, formamide, high_vol_buffer_mix_tube, disposal_vol=0, blow_out=True)
    p300_single.distribute(DNTP_VOL, dntp, high_vol_buffer_mix_tube, disposal_vol=0, blow_out=True)
    p300_single.distribute(SYBR_VOL, sybr, high_vol_buffer_mix_tube, disposal_vol=0, blow_out=True)

    # Add taq last and mix
    p300_single.pick_up_tip()
    p300_single.transfer(TAQ_VOL, taq, high_vol_buffer_mix_tube, disposal_vol=0, blow_out=True, new_tip='never')
    p300_single.mix(15, 300, rate=mix_rate)
    p300_single.drop_tip()

    # Distribute master mix to separate master mix tubes
    p300_single.distribute(MASTER_MIX_TUBE_VOL, buffer_mix_tube, master_mix_tubes, disposal_vol=0, blow_out=True)

    # Add primers to master mix tubes
    for primer, mm_tube in zip(primers, master_mix_tubes):
        p50_multi.pick_up_tip(location=tiprack2_tracker.next_tip(), presses=1)
        p50_multi.transfer(PRIMER_VOL, primer, mm_tube, disposal_vol=0, blow_out=True, new_tip='never')
        p50_multi.mix(number_of_mixing, 50, rate=mix_rate)
        p50_multi.drop_tip()

    def cdna_dispense_location(plate, start_column, end_column):
        return [(col[0], col[0].from_center(x=0, y=0.03, z=-1.5)) for col in plate.columns(start_column, to=end_column)]

    # Mix cDNA samples then distribute to 96-well plate
    p50_multi.pick_up_tip(location=tiprack2_tracker.next_tip(n=8))
    p50_multi.mix(number_of_mixing, 50, samples, rate=mix_rate)
    p50_multi.distribute(CDNA_VOL, samples, cdna_dispense_location(pcr_plate1, '1', '12'), disposal_vol=3, blow_out=True)
    p50_multi.pick_up_tip(location=tiprack2_tracker.next_tip(n=8))
    p50_multi.distribute(CDNA_VOL, samples, cdna_dispense_location(pcr_plate2, '1', '12'), disposal_vol=3, blow_out=True)
    p50_multi.pick_up_tip(location=tiprack2_tracker.next_tip(n=8))
    p50_multi.distribute(CDNA_VOL, samples, cdna_dispense_location(pcr_plate3, '1', '12'), disposal_vol=3, blow_out=True)

    def master_mix_dispense_location(plate, begin_col, end_col):
        return [(well, well.from_center(x=0, y=0.1, z=0.5)) for col in plate.columns(begin_col, to=end_col) for well in col]

    plates = []
    plates.extend([pcr_plate1]*6)
    plates.extend([pcr_plate2]*6)
    plates.extend([pcr_plate3]*6)
    for plate, master_mix, column in zip(plates, master_mix_tubes, list(range(1, 12+1, 2))*3):
        first_column = str(column)
        second_column = str(column + 1)
        p50_multi.pick_up_tip(location=tiprack2_tracker.next_tip(), presses=1)
        p50_multi.distribute(MASTER_MIX_VOL,
                             master_mix,
                             master_mix_dispense_location(plate, first_column, second_column),
                             disposal_vol=0,
                             blow_out=True)


run_custom_protocol(**{'number_of_mixing': 5, 'mix_rate': 6})
