import pandas as pd
import json


base_folder = '/Volumes/Jun SSD/data'

control_file = base_folder + '/Processing_stage.xlsx'

df = pd.read_excel(control_file, index_col=0)    

with open(base_folder + '/config/master_video.json') as master_file:
    master_data = json.load(master_file)

master_data = [f[:-len('.mp4')] for f in master_data ]


df = df[df.index.isin(master_data)]

control_file2 = base_folder + '/Processing_stage2.xlsx'
df.to_excel(control_file2, index=True)