from opentrons import labware, instruments, robot

tube_rack_2ml = labware.load('opentrons-tuberack-2ml-eppendorf', '2')
tiprack = labware.load('opentrons-tiprack-300ul', '1')


def run_custom_protocol():
    p50_single = instruments.P50_Single(mount='right', tip_racks=[tiprack])

    master_mix_tubes = [well for well in tube_rack_2ml.wells('D3', 'D4')]

    transfer_volume = 50
    volume = 2000
    remaining_vol = 2000
    position = 1
    source_position_offset = 0.5
    source_position = position - source_position_offset
    source_tube = master_mix_tubes[0]
    destination_tube = master_mix_tubes[1]

    p50_single.pick_up_tip()
    while remaining_vol > 0:
        robot.comment(str(source_position))
        source = (source_tube, source_tube.from_center(x=0, y=0, z=source_position))
        destination = (destination_tube, destination_tube.from_center(x=0, y=0, z=-position))
        p50_single.transfer(transfer_volume, source, destination, disposal_vol=0, blow_out=True, new_tip='never')

        if position > -1:
            position -= (transfer_volume/volume)*2  # x2 because tube size is -1 to 1 i.e. a difference of 2
        else:
            position = -1

        source_position = position - source_position_offset

        if source_position < -1:
            source_position = -1

        remaining_vol -= transfer_volume


run_custom_protocol()