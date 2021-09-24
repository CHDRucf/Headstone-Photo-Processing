from fuzzywuzzy import process, fuzz
import date_to_iso
import traceback

states = "Alabama Alaska Arizona Arkansas California Colorado Connecticut Delaware Florida Georgia Hawaii Idaho "
states += "Illinois Indiana Iowa Kansas Kentucky Louisiana Maine Maryland Massachusetts Michigan Minnesota "
states += "Mississippi Missouri Montana Nebraska Nevada New_Hampshire New_Jersey New_Mexico New_York "
states += "North_Carolina North_Dakota Ohio Oklahoma Oregon Pennsylvania Rhode_Island South_Carolina "
states += "South_Dakota Tennessee Texas Utah Vermont Virginia Washington West_Virginia Wisconsin Wyoming"
states = states.upper()
states = states.split()
states = [state.replace("_", " ") for state in states]
states = set(states)

conflicts = "Civil_War Spanish_American_War World_War_I World_War_II Korea Vietnam"
conflicts = conflicts.upper()
conflicts = conflicts.split()
conflicts = [conflict.replace("_", " ") for conflict in conflicts]
conflicts = set(conflicts)

months = set(date_to_iso.months.keys())


debug = False

# Input: a headstone with ocr output stored in headstone.ocr_text
# Output: None
# Operation: Assign values to headstone.text_fields
def categorize_ocr_output(headstone):
    headstone.ocr_text = remove_dummy_characters(headstone.ocr_text)
    ocr_text = headstone.ocr_text

    if debug:
        print(ocr_text)

    if len(ocr_text) == 0:
        return
    elif len(ocr_text) == 1:
        headstone.text_fields['First Name'] = ocr_text[0]
        return

    try:
        state, state_idx = classify(ocr_text, 'state')
    except:
        state, state_idx = '', 100

    try:     
        conflict, conflict_idx = classify(ocr_text, 'conflict')
        if conflict in ('WORLD WAR I', 'WORLD WAR II'):
            conflict = conflict.replace('WORLD WAR ', 'WW')
    except: 
        conflict, conflict_idx = '', 100

    try: 
        birth_date, death_date = find_dates(ocr_text)
    except:
        birth_date, death_date = '', ''

    name_bound = min(state_idx, conflict_idx, 3, len(ocr_text))

    if name_bound == 1:
        headstone.text_fields['First Name'] = ocr_text[0]
    elif name_bound == 2:
        try:
            split_first = ocr_text[0].split()
            if len(split_first) == 2:
                headstone.text_fields['First Name'] = split_first[0]
                headstone.text_fields['Middle Name'] = split_first[1]
            else:
                headstone.text_fields['First Name'] = ocr_text[0]
        except Exception as e:
            headstone.text_fields['First Name'] = ocr_text[0]
            traceback.print_exc()
        
        headstone.text_fields['Surname'] = ocr_text[1]
        
    elif name_bound == 3:
        headstone.text_fields['First Name'] = ocr_text[0]
        headstone.text_fields['Middle Name'] = ocr_text[1]
        headstone.text_fields['Surname'] = ocr_text[2]

    headstone.text_fields['State'] = state
    headstone.text_fields['Conflict'] = conflict
    headstone.text_fields['Birth Date'] = birth_date
    headstone.text_fields['Death Date'] = death_date


def remove_dummy_characters(ocr_text):
    return [x for x in ocr_text if x not in ('', '\x0c', '.', '-')]


# Return the best option from the appropriate category and the index where it was found
# Return ('', 100) if nothing is sufficiently good enough for consideration
def classify(ocr_text, category):
    category = category.lower()

    if category == "state":
        options = states
    elif category == "conflict":
        options = conflicts
    else:
        raise ValueError("category must be 'state' or 'conflict'")

    # For each text element find the option with highest score
    selection_with_score = [process.extract(element.upper(), options, limit=1, scorer=fuzz.ratio)[0] + (i,) for i, element in enumerate(ocr_text)]
    
    # Find the best option overall
    if debug:
        print(selection_with_score)
    selection_with_score.sort(key=lambda x: x[1], reverse=True)
    
    # Return the best option if it is sufficiently accurate
    selection, score, index = selection_with_score[0]

    if score >= 85:
        return selection, index

    return '', 100


# Finds the top two most likely candidates for dates
# Convertes them to ISO using date_to_iso
# Returns the results in the order they appaer
# Returns '' if it can't find one
def find_dates(ocr_text):
    scores = [(date_score(element), i, element) for i, element in enumerate(ocr_text)]

    if debug:
        print(scores)

    scores.sort(key=lambda x: x[0], reverse=True)

    top_two = scores[:2]
    top_two.sort(key=lambda x: x[1])
    top_two = [x[2] for x in top_two if x[0] >= 65]

    birth_date = ''
    death_date = ''

    if len(top_two) == 1:
        death_date, = top_two
        death_date = date_to_iso.date_to_iso(death_date)
    
    elif len(top_two) == 2:
        birth_date, death_date = top_two
        birth_date = date_to_iso.date_to_iso(birth_date)
        death_date = date_to_iso.date_to_iso(death_date)

    return birth_date, death_date



# Returns a score from 0 to 100 on whether the input is a date
def date_score(text):
    miniscores = []
    for part in text.split():
        part_scores = [(month, fuzz.ratio(part, month)) for month in months]
        part_scores.sort(key=lambda x: x[1], reverse=True)
        miniscores.append(part_scores[0])

        if set(part) <= date_to_iso.digits and 1700 <= int(part) <= 2100:
            return 100

    miniscores.sort(key=lambda x: x[1], reverse=True)
    month, score = miniscores[0]

    return score




if __name__ == "__main__":
    ocr_text = ["Jimmy", "Jones", "Forda", "Private 1st Class", "World Waa II", "Aug357 1S 192O", "Jum 6 1944"]
    ocr_text = ['EDMUND', 'WARREN', 'MATHEWS', 'VERMONT', 'S SGT', '851 SYC COMD UNIT', 'WORLD WAR IL', 'OCTOBER 9 898', 'JUNE 2 1956']
    ocr_text = ['ARTHUR LEC', 'TARD', 'MARYLANE', 'SOT USARMY']
    ocr_text = ['CARL OTIS', 'STINNETT', 'ORLAHOMA', 'SEAMAN 2CL', 'U. S. NAVY', 'APRIL 5 1935']
    state = classify(ocr_text, 'state')
    conflict = classify(ocr_text, 'conflict')
    print(state, conflict)
    #birth_date, death_date = find_dates(ocr_text)
