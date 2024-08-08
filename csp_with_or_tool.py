from ortools.sat.python import cp_model
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

# Calculate the start and end times in minutes from midnight for each course
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

# OR-Tools CP-SAT model
model = cp_model.CpModel()

# Define variables for each course section and day
courses_vars = {}
for index, course in filtered_courses_df.iterrows():
    var = model.NewBoolVar(f'{course["CRSNO"]}_{course["CLASS TYPE"]}_{course["DAYS"]}_{course["START_TIME"]}')
    courses_vars[(course["CRSNO"], course["CLASS TYPE"], course["DAYS"], course["DAY_START"], course["DAY_END"])] = var

# Ensure each target course is taken exactly once
for target in target_courses:
    model.Add(
        sum(courses_vars[key] for key in courses_vars if key[0] == target["CRSNO"] and key[1] == target["CLASS TYPE"]) == 1
    )

# Ensure there is at least a 30-minute gap between consecutive classes
for key1 in courses_vars:
    for key2 in courses_vars:
        if key1 != key2:
            if key1[2] == key2[2]:  # Same day
                # Ensure courses do not overlap and have at least a 30-minute gap
                model.AddBoolOr([
                    courses_vars[key1].Not(),
                    courses_vars[key2].Not(),
                    key1[4] + 30 <= key2[3],
                    key2[4] + 30 <= key1[3]
                ])

# Solve the model
solver = cp_model.CpSolver()
status = solver.Solve(model)

# Output the results
if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
    print("Found valid schedules:")
    schedules = []
    for key, var in courses_vars.items():
        if solver.Value(var):
            schedules.append({
                "CRSNO": key[0],
                "CLASS TYPE": key[1],
                "DAYS": key[2],
                "START_TIME": f"{key[3]//60:02d}:{key[3]%60:02d}",
                "END_TIME": f"{key[4]//60:02d}:{key[4]%60:02d}"
            })
    valid_schedules_df = pd.DataFrame(schedules)
    print(valid_schedules_df)
    # Save the valid schedules to an Excel file
    output_path = 'result/Valid_Course_Schedules_ORTools.xlsx'
    valid_schedules_df.to_excel(output_path, index=False)
else:
    print("No valid schedules found that include all target courses.")