import requests
from datetime import datetime, timedelta
from db_utils import verify_password, verify_existing_username, verify_new_username, remove_event_from_database, get_entire_schedule, add_event_to_database

# DECORATORS

# Formats event data into a more aesthetic format, and also into UK time
def format_data(nested_function):
    def inner_wrapper(*args):
        all_data = []
        data = nested_function(*args)
        index = 0
        for eachSport in data['result']:
            index += 1
            event = eachSport['event']
            time_start = datetime.strptime(eachSport['start'], '%Y-%m-%d %H:%M:%S')
            time_end = datetime.strptime(eachSport['end'], '%Y-%m-%d %H:%M:%S')
            uk_time_start = time_start - timedelta(hours=8)
            uk_time_end = time_end - timedelta(hours=8)
            formatted_start_time = uk_time_start.strftime('%d %B %Y - %H:%M:%S')
            formatted_end_time = uk_time_end.strftime('%d %B %Y - %H:%M:%S')
            new_data = {'event_name': event, 'start_event': formatted_start_time, 'end_event': formatted_end_time}
            all_data.insert(index,new_data)
        return all_data

    return inner_wrapper

# Uses the sport_id to call endpoint 2 of the API and return a list of all events and schedules for that sport.
def use_sport_id_to_return_list_of_events(nested_function):
    def inner_wrapper(sport_name):
        sport_id = nested_function(sport_name)
        get_all_specific_events = endpoint_list_of_all_events(sport_id)
        return get_all_specific_events

    return inner_wrapper


# FUNCTIONS (chronological order)

# Verifies that:
# If you are creating a new username, it does not already exist
# or
# If you are logging in with an old username, the username exists, you have inputted it correctly AND that
# you have the correct password.
# The functions within this function are all in db_utils
def username_and_password():
    existing_user = input("Have you used our app before?").lower()
    if existing_user == 'no':
        username = input('Please choose a username')
        verify_new_username(username)
        password = input('Please choose a password')
        print("Let's add some events to your personalised Olympick schedule!")
    elif existing_user == 'yes':
        username = input('Please enter your username')
        verify_existing_username(username)
        password = input('Please enter your password')
        verify_password(username, password)
    return username, password


# Calls endpoint 1 of the API, returns a list of all sports names (and other irrelevant details)
def endpoint_list_of_all_sports():
    all_sports = 'https://olypi.com/sports/?call=GetAllSports'
    response = requests.get(all_sports)
    all_sports_data = response.json()
    return all_sports_data


# Uses the inputted sport name to find the sport's ID for the API (find_sport_id_by_name) - then the decorator
# uses this ID to call the API's second endpoint, to finally return a list of events within that sport.
@use_sport_id_to_return_list_of_events
def find_sport_id_by_name(sport_name):
    all_data = endpoint_list_of_all_sports()
    for sport in all_data['result']:
        if sport['name'] == sport_name:
            return sport['id']

# (This function is part of the decorator used in the above function) Calls endpoint 2 of the API, returns a list of
# all events within that sport and their schedules, which have been formatted to UK time by the decorator.
@format_data
def endpoint_list_of_all_events(sport_id):
    list_of_events = 'https://olypi.com/schedule/?call=SportEvents&id={}'.format(sport_id)
    response = requests.get(list_of_events)
    list_of_events_data = response.json()
    return list_of_events_data

# Presents the entire schedule (get_entire_schedule, a function within db_utils) and then will either add_event or
# remove_event. The steps that follow either "add event" or "remove event" are discussed in further comments.

def add_or_remove_events(username, password):
    print("Here is your current schedule: \n")
    result = get_entire_schedule(username)
    operator = input("Would you like to:\n1. Add more events\n2. Remove some events\n3. Quit")
    if operator == '1':
        sport_name, result = choose_sport_display_events()
        add_events(sport_name, result, username, password)
        add_or_remove_events(username, password)
    elif operator == '2':
        array_remove = remove_event(result)
        remove_event_from_database(username, array_remove)
        add_or_remove_events(username, password)
    elif operator == '3':
        print("Thanks for using Olympick! Bye!")
        quit()

# "Add events" functionality
# Function 1/4: choose_sport_display_events
# Presents list of all sports. User can then choose a sport, which will be used to find the sport's ID by calling
# the API's second endpoint (find_sport_id_by_name) and return a list of events for that sport
# (use_sport_id_to_return_list_of_events). This list is iterated through, and each event is numbered and printed.
# This function returns the name of the sport entered, and the list of events for that sport.

def choose_sport_display_events():
    all_sports = endpoint_list_of_all_sports()
    print("🚩🚦 The names you can choose from are : 🚦 🚩 ")
    for sport in all_sports['result']:
        print("🎖", sport['name'], "🎖")
    sport_name = input("for which sport you would like to know the schedules ? ")
    result = find_sport_id_by_name(sport_name)
    print(f" 🏵🤺🤸🏻‍️🏆 All the schedules for {sport_name} : 🏆🤸🤺🏵‍")
    generator2 = (res for res in result)
    index = 0
    for res in generator2:
        index = index + 1
        print("\n", index, res['event_name'], "\nBegins at: ", res['start_event'], "\nEnds at: ", res['end_event'],
              "\n")
    return sport_name, result

# Function 2/4: add_events
# This function uses the sport's event schedule returned in the last function to call the next one (see explanation
# below).
def add_events(sport_name, result, username, password):
    array = add_specific_event(result)
    add_event_to_database(sport_name, username, array, password)  # inside db_utils

# Function 3/4: add_specific_event
# This function will use the entire list of that sport's events (the 'result') and use zero indexing (as the function
# before presented the events as numbered) to find that event within the list of all the sports' events, and then
# add it to an array.
def add_specific_event(result):
    add_to_database = []
    inputted_string = input("Choose the number of the event(s) you would like to add to your schedule!")
    split_string = inputted_string.split()
    map_events_to_add = map(int, split_string)
    for event in map_events_to_add:
        index = int(event) - 1
        event_to_add = result[index]
        add_to_database = add_to_database + [event_to_add]
        # add_to_database.append(event_to_add)
    return add_to_database

# The fourth (4/4) "add events" function - add_event_to_database - is in the db_utils file. It uses the array
# returned in the last function, and adds all of the events individually into that user's schedule within the database.
# Further explanation is provided in the db_utils file.

# "Remove events" functionality:
# (1/2) Uses the result from get_entire_schedule (within the add_or_remove_events function), and the numbers inputted
# by the user, to index the event within the schedule and creates a list from the details of each event chosen to be
# removed.
def remove_event(result):
    inputted_string = input("Choose the numbers of the event(s) you would like to remove to your schedule!")
    remove_from_database = []
    split_string = inputted_string.split()
    map_events_to_remove = map(int, split_string)
    for event in map_events_to_remove:
        index = int(event) - 1
        event_to_remove = result[index]
        remove_from_database.append(event_to_remove)
    return remove_from_database

# The second (2/2) "remove events" function - remove_event_from_database - is in the db_utils file. It uses the array
# returned in the last function, and removes all of the events individually from that user's schedule within the
# database. Further explanation is provided in the db_utils file.

