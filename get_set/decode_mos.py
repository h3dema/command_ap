import datetime
import pickle


#
# load the MOS file, that contains the conversion basis for the Bunny video used in the experiments
#
mos_file = 'metric-results.p'
mos = pickle.load(open(mos_file, 'rb'))

segmentType_values = [100, 200, 240, 375, 550, 750, 1000, 1500, 2300, 3000, 4300, 5800, 6500, 7000, 7500, 8000, 12000, 17000, 20000]
map_index_to_segmenttype = dict(zip(list(range(1, len(segmentType_values) + 1)), segmentType_values))


def get_mos(index, playing_segment):
    """ based on the information received from the browser, map the video to the MOS
        @param index:
        @param playing_segment:
    """
    segmentType = map_index_to_segmenttype[index]
    global mos
    mos_segment = mos[segmentType]
    mos = mos_segment.iloc[playing_segment]['mos']
    return mos


last_data = {'timestamp': None, 'playing_time': None}


def effective_mos(data):
    eff_mos = 1
    index = data['index']
    segmentType = data['chunkDatasegmentType']
    m = get_mos(index, segmentType)
    if last_data['timestamp'] is not None:
        t1 = datetime.strptime(data['timestamp'], '%Y%m%d%H%M%S')
        t0 = datetime.strptime(last_data['timestamp'], '%Y%m%d%H%M%S')
        interval = (t1 - t0).seconds
        if interval > 0:
            playing_time = data['playing_time'] - last_data['playing_time']
            not_running = max(interval - playing_time, 0)
            eff_mos = (playing_time * m + not_running) / (playing_time + not_running)

    # save for the next iteration
    last_data['playing_time'] = data['playing_time']
    last_data['timestamp'] = data['timestamp']

    return eff_mos
