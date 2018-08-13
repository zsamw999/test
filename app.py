import requests
import time
import re
import os

global group_id, botId, at
group_id = str(os.environ.get('GID'))
botId = str(os.environ.get('BID'))
at = str(os.environ.get('AID'))

def prepare_user_dictionary():
    response = requests.get('https://api.groupme.com/v3/groups?token='+at)
    gdata = response.json()
    i = 0
    for i in range(len(data['response'])):
        if gdata['response'][i]['name'] == 'Testing':
            number_of_messages = gdata['response'][i]['messages']['count']
            members_of_group_data = gdata['response'][i]['members']
            i += 1
    user_dictionary = {}
    i = 0
    while True:
        try:
            user_id = members_of_group_data[i]['user_id']
            nickname = members_of_group_data[i]['nickname']
            user_dictionary[user_id] = [nickname, 0.0, 0.0, 0.0, 0.0, {}, {}, 0.0]
        except IndexError:  
            return user_dictionary
        i += 1
    return user_dictionary

def analyze_group(group_id, user_id_mapped_to_user_data, number_of_messages, search_term, search_id, data):
    message_with_only_alphanumeric_characters = ''
    message_id = 0
    iterations = 0.0
    to_send = ''
    while True:
        for i in range(20):  
            try:
                iterations += 1
                name = data['response']['messages'][i]['name']  
                message = data['response']['messages'][i]['text']  
                message_id = data['response']['messages'][i]['id']  
                try:
                    message_with_only_alphanumeric_characters = re.sub(r'\W+', ' ', str(message))
                except ValueError:
                    pass  
                sender_id = data['response']['messages'][i]['sender_id']  
                list_of_favs = data['response']['messages'][i]['favorited_by']  
                length_of_favs = len(list_of_favs)  
                created = data['response']['messages'][i]['created_at'] 
                created_format = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(created))

                number_of_words_in_message = len(re.findall(r'\w+', str(message_with_only_alphanumeric_characters)))

                if sender_id not in user_id_mapped_to_user_data.keys():
                    user_id_mapped_to_user_data[sender_id] = [name, 0.0, 0.0, 0.0, 0.0, {}, {}, 0.0]

                if user_id_mapped_to_user_data[sender_id][0] == '':
                    user_id_mapped_to_user_data[sender_id][0] = name

                for user_id in list_of_favs:
                    if user_id in user_id_mapped_to_user_data[sender_id][5].keys():
                        user_id_mapped_to_user_data[sender_id][5][user_id] += 1
                    else:
                        user_id_mapped_to_user_data[sender_id][5][user_id] = 1

                for user_id in list_of_favs:
                    for user_id_inner in list_of_favs:
                        if user_id not in user_id_mapped_to_user_data.keys():
                            # leave name blank because this means a user is has liked a message but has yet to be added
                            # to the dictionary. So leave the name blank until they send their first message.
                            user_id_mapped_to_user_data[user_id] = ['', 0.0, 0.0, 0.0, 0.0, {}, {}, 0.0]
                        if user_id == user_id_inner:
                            user_id_mapped_to_user_data[user_id][7] += 1
                            continue  # pass because you don't want to count yourself as sharing likes with yourself
                        try:
                            user_id_mapped_to_user_data[user_id][6][user_id_inner] += 1
                        except KeyError:
                            user_id_mapped_to_user_data[user_id][6][user_id_inner] = 1

                user_id_mapped_to_user_data[sender_id][1] += 1  
                user_id_mapped_to_user_data[sender_id][2] += length_of_favs
                user_id_mapped_to_user_data[sender_id][4] += number_of_words_in_message
                
                if (message is not None) and (message.lower() == search_term.lower()) and (message_id != search_id) and (name != 'MemberBerry'):
                     to_send = ("I 'member " + search_term + " was previously 'membered by " + name + " on " + created_format + ". " + str(length_of_favs) + " likes.")
                     pass
                
            except IndexError:
                if len(to_send) > 0:
                    post_params = { 'bot_id' : botId, 'text': to_send } 
                    requests.post('https://api.groupme.com/v3/bots/post', params = post_params)
                print("COMPLETE")
                print
                for key in user_id_mapped_to_user_data:
                    try:
                        user_id_mapped_to_user_data[key][3] = user_id_mapped_to_user_data[key][2] / user_id_mapped_to_user_data[key][1]
                    except ZeroDivisionError:  # for the case where the user has sent 0 messages
                        user_id_mapped_to_user_data[key][3] = 0
                return user_id_mapped_to_user_data

        if i == 19:
                message_id = data['response']['messages'][i]['id']
                remaining = iterations/(number_of_messages - 1)
                remaining *= 100
                remaining = round(remaining, 2)
                print(str(remaining)+' percent done')
                
        payload = {'before_id': message_id}
        response = requests.get('https://api.groupme.com/v3/groups/'+group_id+'/messages?token='+at, params=payload)
        data = response.json()

while True:
    response = requests.get('https://api.groupme.com/v3/groups/'+group_id+'/messages?token='+at)
    data = response.json()
    if (response.status_code == 200):
        response_messages = response.json()['response']['messages']
        for message in response_messages:
            search_term = message['text']
            search_id = message['id']
            user_dictionary = prepare_user_dictionary()
            user_id_mapped_to_user_data = analyze_group(group_id, user_dictionary, number_of_messages, search_term, search_id, data)
            break
        
        time.sleep(20)
