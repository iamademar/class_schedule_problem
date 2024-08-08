import pandas as pd

# Load the provided CSV file containing the available course schedule
available_courses_path = 'data/Available_Course_Schedule.csv'
available_courses_df = pd.read_csv(available_courses_path)

# Define the list of target courses with their course number (CRSNO) and class type (e.g., Lecture or Lab)
target_courses = [
    {"CRSNO": "AnSc 22n", "CLASS TYPE": "Lec"},
    {"CRSNO": "AnSc 22n", "CLASS TYPE": "Lab"},
    {"CRSNO": "AgSc 13", "CLASS TYPE": "Lec"},
    {"CRSNO": "Biol 22p", "CLASS TYPE": "Lec"},
    {"CRSNO": "Biol 22p", "CLASS TYPE": "Lab"},
    {"CRSNO": "ScSc 12n", "CLASS TYPE": "Lec"},
    {"CRSNO": "AgSc 12", "CLASS TYPE": "Lec"},
    {"CRSNO": "Chem 131", "CLASS TYPE": "Lec"},
    {"CRSNO": "Micr 22", "CLASS TYPE": "Lec"},
    {"CRSNO": "Micr 22", "CLASS TYPE": "Lab"},
    {"CRSNO": "CPrt 22", "CLASS TYPE": "Lec"},
    {"CRSNO": "CPrt 22", "CLASS TYPE": "Lab"},
    {"CRSNO": "PhEd 13n", "CLASS TYPE": "Lec"}
]

# Convert 'START_TIME' and 'END_TIME' columns to datetime.time objects for easier time comparisons
available_courses_df['START_TIME'] = pd.to_datetime(available_courses_df['START_TIME'], format='%H:%M').dt.time
available_courses_df['END_TIME'] = pd.to_datetime(available_courses_df['END_TIME'], format='%H:%M').dt.time

# Calculate the start and end times in minutes from midnight for each course and add as new columns
available_courses_df['DAY_START'] = available_courses_df.apply(
    lambda row: (row['START_TIME'].hour * 60) + row['START_TIME'].minute, axis=1
)
available_courses_df['DAY_END'] = available_courses_df.apply(
    lambda row: (row['END_TIME'].hour * 60) + row['END_TIME'].minute, axis=1
)

# Filter the courses based on specific time constraints and exclusions
def filter_courses(df):
    # Apply conditions to filter out courses that do not meet the time criteria
    df = df[
        (df['DAY_START'] >= 480) &  # Courses starting at or after 8:00 AM
        (df['DAY_END'] <= 1140) &   # Courses ending at or before 7:00 PM
        ~((df['DAY_START'] >= 720) & (df['DAY_END'] <= 780)) &  # Exclude courses during 12:00 PM - 1:00 PM
        ~((df['DAY_START'] >= 960) & (df['DAY_END'] <= 1110) & (df['DAYS'].isin(['W', 'F'])))  # Exclude courses from 4:00 PM - 5:30 PM on W & F
    ]
    return df

# Apply the filter to the available courses dataframe
filtered_courses_df = filter_courses(available_courses_df)

# Function to check if there is at least a 30-minute gap between consecutive classes
def check_gap(schedule):
    # Create a list of tuples with the start and end times of each class
    times = [(row['DAY_START'], row['DAY_END']) for _, row in schedule.iterrows()]
    # Sort the times by the start time
    times are sorted(times, key=lambda x: x[0])
    # Check for gaps of at least 30 minutes between classes
    for i in range(1, len(times)):
        if times[i][0] < times[i-1][1] + 30:
            return False
    return True

# Function to find valid schedules that include all target courses without time conflicts
def find_schedules(target_courses, available_courses):
    schedules = []
    target_crsnos = [(course['CRSNO'], course['CLASS TYPE']) for course in target_courses]

    def build_schedule(current_schedule, remaining_courses):
        if not remaining_courses:
            schedules.append(current_schedule)
            return

        next_course = remaining_courses[0]
        next_sections = available_courses[
            (available_courses['CRSNO'] == next_course[0]) & 
            (available_courses['CLASS TYPE'] == next_course[1])
        ]
        
        for _, section in next_sections.iterrows():
            new_schedule = pd.concat([current_schedule, section.to_frame().T])
            if check_gap(new_schedule):
                build_schedule(new_schedule, remaining_courses[1:])
    
    build_schedule(pd.DataFrame(), target_crsnos)
    
    return schedules

# Find valid schedules that meet the specified criteria
valid_schedules = find_schedules(target_courses, filtered_courses_df)

# Function to annotate schedules with any violations of the specified time rules
def add_violations(schedule):
    violations = []
    for _, row in schedule.iterrows():
        violation = ""
        start_time = row['DAY_START']
        end_time = row['DAY_END']
        
        # Check if the class falls within prohibited times
        if 720 <= start_time <= 780 or 720 <= end_time <= 780:
            violation = "12 PM - 1 PM class included"
        elif start_time < 480 or start_time >= 1140:
            violation = "Class beyond allowed hours (7 AM - 7 PM)"
        elif (start_time >= 960 and end_time <= 1110) and (row['DAYS'] in ['W', 'F']):
            violation = "Class 4:00 PM - 5:30 PM on W/F"
        
        violations.append(violation)
    
    schedule['Violation'] = violations
    return schedule

# Apply the violation check to each valid schedule
valid_schedules_with_violations = [add_violations(schedule) for schedule in valid_schedules]

# Save the valid schedules with violations noted to an Excel file
output_path_with_violations = 'result/Valid_Course_Schedules_with_Violations.xlsx'
if valid_schedules_with_violations:
    with pd.ExcelWriter(output_path_with_violations) as writer:
        for idx, schedule in enumerate(valid_schedules_with_violations):
            schedule.to_excel(writer, sheet_name=f'Option_{idx+1}', index=False)
else:
    print("No valid schedules found that include all target courses.")
