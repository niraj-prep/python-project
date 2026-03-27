import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

CSV_FILE = 'student_marks.csv'
DASHBOARD_FILE = 'academic_dashboard.png'

def generate_dummy_data():
    """Generates a dummy CSV file with 120 students across 5 subjects."""
    np.random.seed(42)
    num_students = 120
    departments = ['Computer Science', 'Mechanical', 'Electrical', 'Civil', 'Business']
    
    # Generate base data
    data = {
        'Student_ID': [f'STU{str(i).zfill(3)}' for i in range(1, num_students + 1)],
        'Department': np.random.choice(departments, num_students),
        'Subject_1': np.random.randint(10, 100, num_students).astype(float),
        'Subject_2': np.random.randint(15, 100, num_students).astype(float),
        'Subject_3': np.random.randint(5, 100, num_students).astype(float),
        'Subject_4': np.random.randint(20, 100, num_students).astype(float),
        'Subject_5': np.random.randint(0, 100, num_students).astype(float)
    }
    
    df = pd.DataFrame(data)
    
    # Introduce some missing values (simulating absent students or missing records)
    for sub in ['Subject_1', 'Subject_2', 'Subject_3', 'Subject_4', 'Subject_5']:
        mask = np.random.rand(num_students) < 0.05
        df.loc[mask, sub] = np.nan
        
    df.to_csv(CSV_FILE, index=False)
    print(f"Generated dummy data: {CSV_FILE}")

def main():
    # 1. Provide Data
    if not os.path.exists(CSV_FILE):
        generate_dummy_data()
        
    print(f"Loading data from {CSV_FILE}...")
    df = pd.read_csv(CSV_FILE)
    
    # 2. Data Cleaning: Handle missing marks by filling with 0
    subjects = ['Subject_1', 'Subject_2', 'Subject_3', 'Subject_4', 'Subject_5']
    print(f"Missing values before cleaning:\n{df[subjects].isnull().sum()}")
    df[subjects] = df[subjects].fillna(0)
    print("Missing values replaced with 0.")
    
    # 3. Calculate GPA and total percentages
    # Assuming each subject is out of 100
    df['Total_Marks'] = df[subjects].sum(axis=1)
    df['Percentage'] = df['Total_Marks'] / len(subjects)
    
    # Calculate a simplified GPA on a 4.0 scale based on percentage
    # Formula: (Percentage / 25) - capped between 0.0 and 4.0
    df['GPA'] = (df['Percentage'] / 25).clip(upper=4.0)
    
    # 4. Identify "at-risk" students (below 40%)
    at_risk_df = df[df['Percentage'] < 40].copy()
    
    print("\n--- Academic Performance Summary ---")
    print(f"Total Students: {len(df)}")
    print(f"Average Overall Percentage: {df['Percentage'].mean():.2f}%")
    print(f"Average Overall GPA: {df['GPA'].mean():.2f}")
    print(f"Number of At-Risk Students (<40%): {len(at_risk_df)}")
    
    if len(at_risk_df) > 0:
        print("\nAt-Risk Students List:")
        print(at_risk_df[['Student_ID', 'Department', 'Percentage', 'GPA']].head())
        if len(at_risk_df) > 5:
            print(f"...and {len(at_risk_df) - 5} more.")
            
    # Save at-risk students for follow-up
    at_risk_df.to_csv('at_risk_students.csv', index=False)
    print("\nSaved at-risk students to 'at_risk_students.csv'.")

    # 5. Generate Matplotlib dashboard
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle('Intelligent Academic Performance Tracker Dashboard', fontsize=16, fontweight='bold')
    
    # Subplot 1: Histogram of grade distribution (Percentage)
    axes[0].hist(df['Percentage'], bins=15, color='skyblue', edgecolor='black')
    axes[0].axvline(df['Percentage'].mean(), color='red', linestyle='dashed', linewidth=1, label=f"Mean: {df['Percentage'].mean():.1f}%")
    axes[0].axvline(40, color='orange', linestyle='dashed', linewidth=2, label="Pass Mark (40%)")
    axes[0].set_title('Distribution of Student Percentages')
    axes[0].set_xlabel('Percentage')
    axes[0].set_ylabel('Number of Students')
    axes[0].legend()
    axes[0].grid(axis='y', alpha=0.75)
    
    # Subplot 2: Bar chart comparing department-wise average performance
    dept_avg = df.groupby('Department')['Percentage'].mean().sort_values(ascending=False)
    # Give diff colors to bars
    colors = plt.cm.viridis(np.linspace(0.4, 0.8, len(dept_avg)))
    dept_avg.plot(kind='bar', ax=axes[1], color=colors, edgecolor='black')
    
    axes[1].set_title('Average Performance by Department')
    axes[1].set_xlabel('Department')
    axes[1].set_ylabel('Average Percentage')
    axes[1].tick_params(axis='x', rotation=45)
    axes[1].grid(axis='y', alpha=0.75)
    
    # Add values on top of bars
    for i, v in enumerate(dept_avg):
        axes[1].text(i, v + 1, f"{v:.1f}%", ha='center', va='bottom', fontweight='bold')
    
    plt.tight_layout()
    plt.subplots_adjust(top=0.88) # Adjust title spacing
    
    # Save the dashboard
    plt.savefig(DASHBOARD_FILE, dpi=300)
    print(f"\nDashboard saved successfully as '{DASHBOARD_FILE}'.")
    
if __name__ == '__main__':
    main()
