import requests
import time
import re
import os	
import pandas as pd
from datetime import date, datetime, timedelta

global group_id, botId, at
group_id = str(os.environ.get('GID'))
botId = str(os.environ.get('BID'))
at = str(os.environ.get('AID'))
chid = str(os.environ.get('CID'))

def load_messages(search_name, search_message, search_message_clean, search_message_id, search_message_dt, response_messages, total_messages):
    message_id = 0
    progress = 0.0
    counted = 0
    df = pd.DataFrame()
    temp = pd.DataFrame()
    today_stamp = time.time()
    rules = [search_name != 'MemberBerry',
             today_stamp <= search_message_dt + 3601,
             search_message_clean.lower() not in ('wrongthread','dhatp','flabongo','flabango','autolike','hofer','rip'),
             search_message_clean.lower() not in ('haha','ha','hilarious','lol','wow','yes'),
             search_message_clean.lower() not in ('goodone','sogood','greatone','thatsagoodone','niceone','somanyguys'),
             search_message_clean.lower() not in ('loser','fuck','damnit','dammit','fuckyoumemberberry','gotohellmemberberry')
             ]

    if all(rules):    
        while counted < total_messages:
            temp = pd.DataFrame(response_messages)
            temp['created_format'] = pd.to_datetime(temp['created_at'],  unit='s', )
            temp['text_clean'] = temp['text'].str.replace('\W', '')
            df = df.append(temp[['id','created_at','created_format','name','text','text_clean','favorited_by']], ignore_index = True)
            counted = counted + 99
            progress = round(counted / total_messages * 100,2)    
            oldest = temp['created_at'].min()
            oldest_format = str(temp['created_format'].iloc[-1])
            print(str(progress) + '%  ' + str(oldest_format))
            message_id = str(temp['id'].iloc[-1])
            
            if counted < total_messages:
                payload = {'before_id': message_id}
                response = requests.get('https://api.groupme.com/v3/groups/'+group_id+'/messages?token='+at+'&limit=100', params=payload)
                response_messages = response.json()['response']['messages']

        if df['text_clean'].str.contains(search_message_clean, case=False, na=False).sum() > 0:
            print("potential matches")
            df_search = pd.DataFrame(df['text_clean'].str.contains(search_message_clean, case=False, na=False))
            df_search.reset_index(inplace=True)
            df_filter = pd.DataFrame(df_search['index'][(df_search['text_clean'] == True)])
            df_join = df_filter.join(df, how='left')        
            load_memberberry(df_join, search_name, search_message, search_message_clean, search_message_id)
    else: 
        print("RULE BREAK")
           
def load_memberberry(df_join, search_name, search_message, search_message_clean, search_message_id):
    to_send = ''
    i = 0
    for i in range(len(df_join)):    
        message = df_join['text_clean'].iloc[i]
        name = df_join['name'].iloc[i]  
        message_id = df_join['id'].iloc[i]
        created_format = df_join['created_format'].iloc[i]
        length_of_favs = len(df_join['favorited_by'].iloc[i])
    
        if (message is not None) and (message.lower() == search_message_clean.lower()) and (message_id != search_message_id) and (name != 'MemberBerry'):
            to_send = ("I 'member " + search_message + " was previously 'membered by " + name + " on " + str(created_format) + ". " + str(length_of_favs) + " likes.")
            #print("criteria: " + to_send)
            pass
        i += 1
        
    if len(to_send) > 0:
        post_params = { 'bot_id' : botId, 'text': to_send } 
        requests.post('https://api.groupme.com/v3/bots/post', params = post_params)
        to_send = ''
    print("COMPLETE: " + to_send)
    to_send = ''

while True:
    response = requests.get('https://api.groupme.com/v3/groups/'+group_id+'/messages?token='+at+'&limit=100')
    if (response.status_code == 200):
        response_messages = response.json()['response']['messages']
        total_messages = response.json()['response']['count']
        for message in response_messages:
            if message['text'] is not None:
                search_name = message['name']  
                search_message = message['text']
                search_message_clean = re.sub(r'\W+', '', str(search_message))
                search_message_id = message['id']
                search_message_dt = message['created_at']
                load_messages(search_name, search_message, search_message_clean, search_message_id, search_message_dt, response_messages, total_messages)
                break       
        time.sleep(10)
