from opentrons import labware, instruments, robot

tube_rack_2ml = labware.load('opentrons-tuberack-2ml-eppendorf', '2')
tiprack = labware.load('opentrons-tiprack-300ul', '1')


def run_custom_protocol():
    p50_single = instruments.P50_Single(mount='right', tip_racks=[tiprack])

    transfer_volume = 50
    initial_volume = 2000  # Initial volume held in source tube

    source_tube = tube_rack_2ml.wells('D3')
    destination_tube = tube_rack_2ml.wells('D4')

    remaining_vol = 2000
    height = 1  # Initial height within source tube
    source_height_offset = 0.5  # Offset so that pipette tip is slightly submerged in source tube, not hovering at surface
    source_height = height - source_height_offset
    p50_single.pick_up_tip()
    while remaining_vol > 0:
        robot.comment(str(source_height))  # Print out the current source_height

        # This transfer command will start pipetting from the top of the source tube to the bottom of the destination
        # tube, and will continue "tracking" the height of the two volumes in each tube
        source = (source_tube, source_tube.from_center(x=0, y=0, z=source_height))  # locations are tuples
        destination = (destination_tube, destination_tube.from_center(x=0, y=0, z=-height))  # locations are tuples
        p50_single.transfer(transfer_volume, source, destination, disposal_vol=0, blow_out=True, new_tip='never')

        # Update height by subtracting ratio of transfer_vol:inital_vol, or set to bottom of tube is "below" bottom
        if height > -1:
            height -= (transfer_volume/initial_volume)*2  # x2 because tube size is -1 to 1 i.e. a difference of 2
        else:
            height = -1

        # Update source_height or set to bottom of tube
        source_height = height - source_height_offset
        if source_height < -1:
            source_height = -1

        # Update remaining volume
        remaining_vol -= transfer_volume


run_custom_protocol()