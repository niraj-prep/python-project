from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

REQUIRED_COLUMNS = ["Sr. No.", "Roll No", "Name of Student", "Section"]
RISK_THRESHOLD = 40.0

# Update these values if your institute uses a different marking scheme.
SUBJECT_MAX_MARKS = {
    "Statistics & Probability": 40,
    "Object Oriented Programming": 40,
    "Operating Systems": 40,
    "Business Communication": 20,
    "Data Analysis and Visualization": 40,
    "Fundamentals of Accounting": 40,
    "Sensors and Actuators": 20,
    "Basics Of Human Computer Interaction": 40,
    "Electric Vehicle": 40,
    "Game Development Using Python": 40,
    "Operation Research": 40,
    "Wireless Sensor Network": 40,
}


def validate_input_columns(df):
    """Validate required columns and ensure max marks are defined for each subject."""
    missing_columns = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_columns:
        raise ValueError(
            "Missing required column(s): " + ", ".join(missing_columns)
        )

    subject_cols = [col for col in df.columns if col not in REQUIRED_COLUMNS]
    missing_subject_max_marks = [
        col for col in subject_cols if col not in SUBJECT_MAX_MARKS
    ]
    if missing_subject_max_marks:
        raise ValueError(
            "Add max marks for subject(s): " + ", ".join(missing_subject_max_marks)
        )

    return subject_cols


def clean_data(df, subject_cols):
    """Clean marks, convert absences to zero, and track absences separately."""
    absent_mask = df[subject_cols].apply(
        lambda col: col.astype(str).str.strip().str.upper().eq("AB")
    )

    df[subject_cols] = df[subject_cols].replace({"AB": 0, "ab": 0})
    for col in subject_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["Absent_Count"] = absent_mask.sum(axis=1)
    return df, absent_mask


def list_weak_subjects(weak_subject_row):
    """Convert a boolean weak-subject row into a readable comma-separated string."""
    weak_subjects = weak_subject_row[weak_subject_row].index.tolist()
    return ", ".join(weak_subjects) if weak_subjects else "None"


def calculate_performance(df, subject_cols):
    """Calculate percentages, GPA, and at-risk flags using fixed max marks."""
    subject_max_marks = pd.Series(
        {col: SUBJECT_MAX_MARKS[col] for col in subject_cols}, dtype="float64"
    )
    subject_percentages = df[subject_cols].div(subject_max_marks, axis=1).mul(100).round(2)

    weak_subject_mask = subject_percentages.lt(RISK_THRESHOLD)

    df["Percentage"] = subject_percentages.mean(axis=1, skipna=True).fillna(0).round(2)
    df["GPA"] = (df["Percentage"] / 10).round(2)
    df["Weak_Subject_Count"] = weak_subject_mask.sum(axis=1)
    df["Weak_Subjects"] = weak_subject_mask.apply(list_weak_subjects, axis=1)
    df["At_Risk"] = df["Percentage"] < RISK_THRESHOLD

    return df, subject_percentages, subject_max_marks


def build_subject_summary(df, subject_cols, subject_percentages, subject_max_marks, absent_mask):
    """Build subject-wise weak-performance analysis."""
    students_with_marks = df[subject_cols].notna().sum()
    below_threshold_count = subject_percentages.lt(RISK_THRESHOLD).sum()
    below_threshold_percentage = (
        below_threshold_count / students_with_marks.replace(0, pd.NA) * 100
    ).round(2).fillna(0)

    subject_summary = pd.DataFrame(
        {
            "Subject": subject_cols,
            "Max_Marks": subject_max_marks.reindex(subject_cols).astype(int).values,
            "Students_With_Marks": students_with_marks.reindex(subject_cols).astype(int).values,
            "Average_Percentage": subject_percentages.mean().reindex(subject_cols).round(2).fillna(0).values,
            "Below_40_Count": below_threshold_count.reindex(subject_cols).astype(int).values,
            "Below_40_Percentage": below_threshold_percentage.reindex(subject_cols).values,
            "Absent_Count": absent_mask.sum().reindex(subject_cols).astype(int).values,
        }
    )

    return subject_summary.sort_values(
        by=["Below_40_Percentage", "Average_Percentage"],
        ascending=[False, True],
    ).reset_index(drop=True)


def build_at_risk_export(df):
    """Create a focused CSV for students below the risk threshold."""
    export_columns = [
        "Roll No",
        "Name of Student",
        "Section",
        "Percentage",
        "GPA",
        "Absent_Count",
        "Weak_Subject_Count",
        "Weak_Subjects",
    ]

    at_risk_students = df[df["At_Risk"]].copy()
    return at_risk_students.sort_values(
        by=["Percentage", "Weak_Subject_Count", "Absent_Count"],
        ascending=[True, False, False],
    )[export_columns]


def annotate_bars(ax, formatter):
    """Add labels on top of bars for quick reading."""
    for patch in ax.patches:
        value = patch.get_width() if patch.get_width() > patch.get_height() else patch.get_height()
        if patch.get_width() > patch.get_height():
            ax.annotate(
                formatter(value),
                (patch.get_width(), patch.get_y() + patch.get_height() / 2),
                ha="left",
                va="center",
                xytext=(5, 0),
                textcoords="offset points",
                fontsize=10,
            )
        else:
            ax.annotate(
                formatter(value),
                (patch.get_x() + patch.get_width() / 2, patch.get_height()),
                ha="center",
                va="bottom",
                xytext=(0, 5),
                textcoords="offset points",
                fontsize=10,
            )


def generate_dashboard(df, subject_summary, dashboard_path):
    """Generate a dashboard with overall, section, and subject risk views."""
    sns.set_theme(style="whitegrid")

    fig, axes = plt.subplots(2, 2, figsize=(16, 10))

    sns.histplot(df["Percentage"], bins=15, kde=True, color="#4c72b0", ax=axes[0, 0])
    axes[0, 0].set_title("Distribution of Student Percentages", fontsize=14, fontweight="bold")
    axes[0, 0].set_xlabel("Percentage (%)")
    axes[0, 0].set_ylabel("Number of Students")
    axes[0, 0].axvline(
        RISK_THRESHOLD,
        color="#c44e52",
        linestyle="dashed",
        linewidth=2.5,
        label=f"At-Risk Threshold (< {RISK_THRESHOLD:.0f}%)",
    )
    axes[0, 0].legend(fontsize=10)

    section_avg = df.groupby("Section", as_index=False)["Percentage"].mean()
    sns.barplot(x="Section", y="Percentage", data=section_avg, color="#55a868", ax=axes[0, 1])
    axes[0, 1].set_title("Average Performance by Section", fontsize=14, fontweight="bold")
    axes[0, 1].set_xlabel("Section")
    axes[0, 1].set_ylabel("Average Percentage (%)")
    axes[0, 1].set_ylim(0, 100)
    annotate_bars(axes[0, 1], lambda value: f"{value:.1f}%")

    top_subjects = subject_summary.head(6).sort_values("Below_40_Percentage")
    sns.barplot(
        x="Below_40_Percentage",
        y="Subject",
        data=top_subjects,
        color="#c44e52",
        ax=axes[1, 0],
    )
    axes[1, 0].set_title("Subjects With Highest Weak Performance", fontsize=14, fontweight="bold")
    axes[1, 0].set_xlabel("Students Below 40% (%)")
    axes[1, 0].set_ylabel("")
    annotate_bars(axes[1, 0], lambda value: f"{value:.1f}%")

    section_risk = df.groupby("Section", as_index=False)["At_Risk"].sum()
    section_risk = section_risk.rename(columns={"At_Risk": "At_Risk_Count"})
    sns.barplot(x="Section", y="At_Risk_Count", data=section_risk, color="#8172b2", ax=axes[1, 1])
    axes[1, 1].set_title("At-Risk Students by Section", fontsize=14, fontweight="bold")
    axes[1, 1].set_xlabel("Section")
    axes[1, 1].set_ylabel("At-Risk Student Count")
    annotate_bars(axes[1, 1], lambda value: f"{int(value)}")

    plt.tight_layout()
    plt.savefig(dashboard_path, dpi=300)
    plt.close(fig)
    print(f"Dashboard successfully generated and saved to '{dashboard_path.resolve()}'.")


def main():
    base_dir = Path(__file__).resolve().parent
    file_path = base_dir / "student.csv"

    if not file_path.exists():
        print(f"Error: The input file '{file_path.resolve()}' was not found.")
        return

    print(f"Loading data from '{file_path.resolve()}'...")
    df = pd.read_csv(file_path)
    print(f"Successfully loaded {len(df)} student records.")

    try:
        subject_cols = validate_input_columns(df)
    except ValueError as exc:
        print(f"Error: {exc}")
        return

    print("Cleaning data, tracking absences, and converting marks...")
    df, absent_mask = clean_data(df, subject_cols)

    print("Calculating percentages, GPA, and weak-subject analysis...")
    df, subject_percentages, subject_max_marks = calculate_performance(df, subject_cols)
    subject_summary = build_subject_summary(
        df, subject_cols, subject_percentages, subject_max_marks, absent_mask
    )

    at_risk_students = build_at_risk_export(df)
    at_risk_count = int(df["At_Risk"].sum())

    print("-" * 50)
    print(f"Total students processed: {len(df)}")
    print(f"Average Overall Percentage: {df['Percentage'].mean():.2f}%")
    print(
        f"Total Students At-Risk (<{RISK_THRESHOLD:.0f}%): "
        f"{at_risk_count} ({(at_risk_count / len(df)) * 100:.1f}%)"
    )
    print("Highest-risk subjects:")
    for row in subject_summary.head(5).itertuples(index=False):
        print(
            f"- {row.Subject}: {row.Below_40_Percentage:.1f}% below 40%, "
            f"avg {row.Average_Percentage:.1f}%"
        )
    print("-" * 50)

    output_csv = base_dir / "processed_students.csv"
    df.to_csv(output_csv, index=False)
    print(f"Processed tabular data saved to '{output_csv.resolve()}'.")

    at_risk_csv = base_dir / "at_risk_students.csv"
    at_risk_students.to_csv(at_risk_csv, index=False)
    print(f"At-risk student data saved to '{at_risk_csv.resolve()}'.")

    subject_summary_csv = base_dir / "subject_performance_summary.csv"
    subject_summary.to_csv(subject_summary_csv, index=False)
    print(f"Subject performance summary saved to '{subject_summary_csv.resolve()}'.")

    print("Generating Matplotlib dashboard...")
    dashboard_path = base_dir / "dashboard.png"
    generate_dashboard(df, subject_summary, dashboard_path)
    print("Execution completed successfully.")


if __name__ == "__main__":
    main()
