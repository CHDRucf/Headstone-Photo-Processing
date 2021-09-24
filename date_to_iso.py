from fuzzywuzzy import process
import enum

months = {"JANUARY":1,
          "FEBRUARY":2,
          "MARCH":3,
          "APRIL":4,
          "MAY":5,
          "JUNE":6,
          "JULY":7,
          "AUGUST":8,
          "SEPTEMBER":9,
          "OCTOBER":10,
          "NOVEMBER":11,
          "DECEMBER":12
        }

letters = 'abcdefghijklmnopqrstuvwxyz'
letters = set(letters + letters.upper())
digits = set('1234567890')
valid = letters ^ digits

class Part(enum.Enum):
        year = 0
        month = 1
        day = 2
        month_or_day = 3
        month_or_year = 4
        unknown = 5

def month_name_to_number(month):
    # Check if the month is already a number
    try:
        if 0 < int(month) < 13:
            return month
    except:
        pass

    return months[process.extract(month.upper(), months.keys(), limit=1)[0][0]]


def create_iso(year, month, day):
    try:
        year = int(year)
        year = f'{year:04}'
    except:
        pass

    try:
        month = int(month)
        month = f'{month:02}'
    except:
        pass

    try:
        day = int(day)
        day = f'{day:02}'
    except:
        pass

    output = f'{year}-{month}-{day}'
    
    if output == '--':
        return ''

    return output

def check_iso(date):
    try:
        date = date.split('-')
        if len(date) != 3:
            return False
        year, month, day = tuple(date)
        if not 1700 < int(year) < 2100:
            return False
        if not (0 < int(month) < 13 and len(month) == 2): 
            return False
        if not (0 < int(day) < 31 and len(day) == 2):
            return False
        return True
    except Exception:
        return False

def classify_part(part):
    # Check for year and day
    if set(part) <= digits:
        part = int(part)
        if 1700 < part < 2100:
            return Part.year
        elif 13 <= part <= 31:
            return Part.day
        elif 31 < part:
            return Part.month_or_year
        else:
            return Part.month_or_day
   
    # Check for month
    elif set(part) <= letters:
        return Part.month

    else:
        return Part.unknown
    

def date_to_iso(date):
    # Check if it's already ISO
    if check_iso(date):
        return date

    # Extract bad characters
    # Replace all bad characters with dashes
    date = ''.join([c if c in valid else "-" for c in date])
    # Split on the dashes
    date = date.split("-")
    # Remove empty strings
    date = [s for s in date if s != '']

    # Pain
    parts = [classify_part(part) for part in date]
    year = ''
    month = ''
    day = ''

    #print(parts, date)

    for part, s in zip(parts, date):
        if part == Part.year and year == '':
            year = s
        elif part == Part.day and day == '':
            day = s
        elif part == Part.month and month == '':
            month += s

    for part, s in zip(parts, date):
        if part == Part.month_or_day:
            if month != '' or day == '':
                day = s
            else:
                month += s
        if part == Part.month_or_year:
            if month != '' or year == '':
                year = s
            else:
                month += s
    
    for part, s in zip(parts, date):
        if part == Part.unknown:
            if year == '':
                year = s
            elif month == '':
                month = s
            elif day == '':
                day = s

    if month != '':
        month = month_name_to_number(month)
    return create_iso(year, month, day)




if __name__ == "__main__":
    l = ["1862-06-04",
         "June 4 1862",
         "Ju.ne 4 1862",
         "June 4 1B62",
         "6/4/1862",
         "1862",
         "June 1862",
         "June",
         "15 1967",
         "APRIL 14 19-48",
         "19-48 APRIL 14"
        ]

    for s in l:
        print(s, '\t', date_to_iso(s))