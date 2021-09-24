import pandas as pd
from fuzzywuzzy import fuzz
import time
from global_vars import global_vars, slash
import exceptions
from headstone import Headstone
import numpy as np
import threading
import os
from functools import wraps

df = None
dicts_df = None
lock = threading.Lock()


# Decorator function to allow only one thread access to a function at a time
# Every locked function shares the same lock
def locked(func):
    @wraps(func)
    def inner(*args, **kwargs):
        lock.acquire()
        try:
            ret = func(*args, **kwargs)
        except Exception as e:
            raise e
        else:
            return ret
        finally:
            lock.release()
    return inner

# The reverse of locked
# Necessary for recursive calls
def unlocked(func):
    def inner(*args, **kwargs):
        lock.release()
        try:
            ret = func(*args, **kwargs)
        except Exception as e:
            raise e
        else:
            return ret
        finally:
            lock.acquire()
    return inner


# If lableable: assign label and fuzziness_score to headstone
# Otherwise, raises a LabelError
# No return value (defaults to None)
@locked
def driver_labeling(headstone):
    match_df = get_fuzzy_matches(headstone)

    # Empty data frame, no matches
    if match_df is None:
        raise exceptions.LabelError(exceptions.LabelError.Situations.No_Matches)

    best_score = match_df.iloc[0]['Fuzziness']
    second_best_score = match_df.iloc[1]['Fuzziness']
    best_index = match_df.iloc[0].name
    df_dict = dict(df.iloc[best_index])
    label = global_vars.options["Label Format"].format(df_dict)
    
    # Perfect Match
    if best_score == 100:

        # Multiple Perfect Matches
        if second_best_score == 100:
            raise exceptions.LabelError(exceptions.LabelError.Situations.Multiple_Perfect)

        headstone.fuzziness_score = best_score
        headstone.set_label(label)

        # Entry already assigned, must reassign
        if 0 < df.loc[best_index, 'Fuzziness'] < best_score:
            df.loc[best_index, 'Fuzziness'] = best_score
            reassign(best_index)

        # No reassign needed
        else:
            df.loc[best_index, 'Fuzziness'] = best_score

        return

    # All matches below threshold (AKA: No Matches)
    if best_score < global_vars.options["Fuzziness Threshold"]:
        raise exceptions.LabelError(exceptions.LabelError.Situations.No_Matches)

    # Fuzzy Tie: Identically-Scoring Non-Perfect Matches
    if best_score - second_best_score < 1:
        raise exceptions.LabelError(exceptions.LabelError.Situations.Fuzzy_Tie)

    if best_score - second_best_score < global_vars.options["Confirmation Tolerance"] and global_vars.options["Fuzzy Matches"] == "Request Confirmation":
        raise exceptions.LabelError(exceptions.LabelError.Situations.Too_Close_To_Call)

    # Driver not permitted to approve fuzzy matches
    if global_vars.options["Fuzzy Matches"] == "Reject":
        raise exceptions.LabelError(exceptions.LabelError.Situations.Fuzzy)

    # Driver IS permitted to approve fuzzy matches
    headstone.fuzziness_score = best_score
    headstone.set_label(label)

    # Entry already assigned, must reassign
    if 0 < df.loc[best_index, 'Fuzziness'] < best_score:
        df.loc[best_index, 'Fuzziness'] = best_score
        reassign(best_index)

    # No reassign needed
    else:
        df.loc[best_index, 'Fuzziness'] = best_score


# Returns a pandas dataframe containing at most 5 records from the datafile, 
# in descending order of fuzziness
@locked
def feedback_labeling(headstone):
    match_df = get_fuzzy_matches(headstone)
    #match_df = match_df[match_df["Fuzziness"] >= 50]
    return match_df


# Sets the fuzziness score of an entry
@locked
def set_fuzziness(entry, score):
    # First need to find the index (row name) of the entry in the dataframe
    tempdf = df
    for k, v in entry.items():
        tempdf = tempdf[tempdf[k] == v]
        if len(tempdf) == 1:
            break

    if len(tempdf) != 1:
        return

    index = tempdf.iloc[0].name

    # Once index is determined, just set the score

    # Entry already assigned, must reassign
    if 0 < df.loc[index, 'Fuzziness'] < score:
        df.loc[index, 'Fuzziness'] = score
        reassign(index)

    # No reassign needed
    else:
        df.loc[index, 'Fuzziness'] = score


# Calculate the fuzziness score of a headstone, based on its text fields, for each entry in the data file
# Fuzziness score is an integer from 0 to 100, where 100 is a perfect match of available data
# Sort scores, return the top num_matches scores as a pandas dataframe
# Returns None if headstone text fields are blank
def get_fuzzy_matches(headstone, num_matches=5):
    global dicts_df

    fields = get_evaluatable_fields(headstone)

    if len(fields) == 0:
        return None

    dict_headstone = {k:headstone.text_fields[k] for k in fields}

    fuzz_scores = [get_fuzziness_score_one_entry(dict_headstone, entry) for entry in dicts_df]

    fields_and_scores = df.assign(Fuzziness = fuzz_scores)
    fields_and_scores = fields_and_scores.sort_values(by=["Fuzziness"], ascending=False)


    return fields_and_scores[0:num_matches]



# Return a list of the columns of the data file,
# that have a corresponding field of the headstone
# for which we have data 
def get_evaluatable_fields(headstone):
    fields = list(Headstone.text_field_keys)
    columns = list(df.columns)

    for key in Headstone.text_field_keys:
        if key not in columns or headstone.text_fields[key] == "":
            fields.remove(key)

    return fields


# Overall fuzziness score is the average of the scores for each field
# Perfect matches on a field are waited double if they are longer than 1 character
# If the final result is less than a fuzziness score already recorded in the dataframe,
#   the entry must already be in use by something better; therefore, return 0
# guess: an OrderedDict of the fields on the headstone
# entry: an OrderedDict of the fields in a data file entry
# Precondition: entry has all the same keys as guess, and potentially more
# Returns the fuzz ratio for guess and entry
def get_fuzziness_score_one_entry_ordered(guess, entry):
    #field_scores = list()
    total_score = 0
    num_scores = len(guess.keys())
    for k in guess.keys():
        score = fuzz.ratio(str(guess[k]).upper(), str(entry[k]).upper())
        #field_scores.append(score)
        total_score += score
        if score == 100 and len(str(guess[k])) > 1 and len(str(entry[k])) > 1:
            #field_scores.append(score)
            total_score += score
            num_scores += 1
    
    #final_score = sum(field_scores) / len(field_scores)
    final_score = total_score / num_scores
    if final_score < entry['Fuzziness']:
        final_score = 0
    return final_score


def get_fuzziness_score_one_entry_unordered(guess, entry):
    keys = list(guess.keys())
    guess_string = ' '.join([str(guess.get(k, '')).upper() for k in keys])
    entry_string = ' '.join([str(entry.get(k, '')).upper() for k in keys])
    score = fuzz.token_set_ratio(guess_string, entry_string)
    if score < entry['Fuzziness']:
        score = 0
    return score 


def get_fuzziness_score_one_entry(guess, entry):
    ordered = get_fuzziness_score_one_entry_ordered(guess, entry)
    unordered = get_fuzziness_score_one_entry_unordered(guess, entry)
    score = 0.1 * ordered + 0.9 * unordered
    return round(score, 1)


# Reassign the image currently assigned to the entry located at 'index' to a different entry
@unlocked
def reassign(index):
    entry_dict = dict(df.iloc[index])
    label = global_vars.options["Label Format"].format(entry_dict)
    path = global_vars.parameters["Destination Folder"] + slash + label + '.JPG'
    headstone = Headstone.load(path)
    try:
        driver_labeling(headstone)
    except exceptions.LabelError as e:
        headstone.error = e
        headstone.log_event("Encountered exception '{}' during reassignment".format(str(e)))
        headstone.label = Headstone.extract_filename(headstone.original_path)[1:]
        headstone.move("Feedback Folder", target="MODIFIED", apply_label=True)
        headstone.label = None
        headstone.save()
        global_vars.feedback_queue.append(headstone.modified_path)
    else:
        headstone.error = None
        headstone.log_event("Reassigned successfully with label '{}'".format(headstone.label))
        headstone.move("Destination Folder", target="MODIFIED", apply_label=True)
        headstone.save()



# Load the data from the data file into the global df variable
# Does nothing if it's already loaded
# Also load the global log
@locked
def load_data():
    global df
    global dicts_df
    if df is None:
        data_file = global_vars.parameters.get("Data File")
        df = pd.read_csv(data_file)
        df = df.replace(np.nan, '', regex=True)
        if 'Fuzziness' not in df.columns:
            df = df.assign(Fuzziness = [0] * len(df))
    if dicts_df is None:
        dicts_df = dicts_df = df.to_dict(orient="records")
    
    try:
        with open(global_vars.parameters["Log File"], 'r') as f:
            old_log = f.read()
        if old_log != '':
            logs = [log for log in old_log.split('\n') if log != '']
            last_log = logs[-1] if len(logs) > 0 else ''
            global_vars.prev_log = last_log.split('\t')[0]
    except FileNotFoundError as e:
        pass


# Save the data back into the CSV
# important for the fuzziness data
# Also save the global log
@locked
def write_data():
    global df
    if df is not None:
        data_file = global_vars.parameters.get("Data File")
        if os.path.isfile(data_file):
            os.remove(data_file)
        df.to_csv(data_file, index=False)

    with open(global_vars.parameters["Log File"], 'a') as f:
        f.write(global_vars.log)


