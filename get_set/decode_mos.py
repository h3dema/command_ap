import os
from datetime import datetime
import pickle
import numpy as np

import logging
LOG = logging.getLogger('SERVER_FFOX')


#
# load the MOS file, that contains the conversion basis for the Bunny video used in the experiments
#
__dir = os.path.dirname(__file__)
__mos_file = 'metric-results.p'
mos = pickle.load(open(os.path.join(__dir, __mos_file), 'rb'))

segmentType_values = [100, 200, 240, 375, 550, 750, 1000, 1500, 2300, 3000, 4300, 5800, 6500, 7000, 7500, 8000, 12000, 17000, 20000]
map_index_to_segmenttype = dict(zip(list(range(1, len(segmentType_values) + 1)), segmentType_values))


def get_mos(index, playing_segment):
    """ based on the information received from the browser, map the video to the MOS
        @param index:
        @param playing_segment:
    """
    global mos
    segmentType = map_index_to_segmenttype[index]
    # LOG.info('** index {} playing_segment {}'.format(index, playing_segment))
    # LOG.info('** segmentType {} {}'.format(segmentType, type(segmentType)))
    mos_segment = mos[segmentType]
    r = mos_segment.iloc[playing_segment]['mos']
    return r


last_data = {'timestamp': None, 'playing_time': None}


def effective_mos(data):
    eff_mos = 1
    index = data.get('index', -1)
    max_index = data.get('maxIndex', index)
    segment = np.ceil(data.get('playing_time', -1)).astype(int)
    LOG.debug("Find MOS at ({}/{}, {}): {}".format(index, max_index, segment, data))
    if index > 0 and index <= max_index and segment > 0:
        # LOG.info('>>** index {} playing_segment {}'.format(index, segment))
        m = get_mos(index, segment)
        # LOG.info(last_data['timestamp'] is not None)
        if last_data['timestamp'] is not None:
            t1 = datetime.strptime(data['timestamp'], '%Y%m%d%H%M%S')
            t0 = datetime.strptime('last_data'['timestamp'], '%Y%m%d%H%M%S')
            interval = (t1 - t0).seconds
            LOG.debug("t1: {} t0:{} interval:{} - index mos {}".format(t1, t0, interval, m))
            if interval > 0:
                playing_time = np.abs(data['playing_time'] - last_data['playing_time'])
                not_running = max(interval - playing_time, 0)
                eff_mos = (playing_time * m + not_running) / (playing_time + not_running)

        # save for the next iteration
        # LOG.info("************ SAVED {}".format(data['timestamp']))
        last_data['playing_time'] = data['playing_time']
        last_data['timestamp'] = data['timestamp']
        LOG.debug("{} Effetive MOS: {}".format(last_data['timestamp'], eff_mos))

    return eff_mos
