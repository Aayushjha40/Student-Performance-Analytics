
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="Student Performance Analytics",
    page_icon="📊",
    layout="wide",
)

BASE_DIR = Path(__file__).resolve().parents[1]
RESULTS_DIR = (
    BASE_DIR
    / "data"
    / "processed"
    / "department_summary"
)

st.title("📊 Student Performance Analytics")
st.caption("Department-level insights powered by Apache Spark and Hadoop HDFS")

csv_files = list(RESULTS_DIR.glob("part-*.csv"))

if not csv_files:
    st.error(
        "No Spark results found. Run the Spark analytics job first."
    )
    st.stop()

df = pd.read_csv(csv_files[0])

# Sidebar filters
st.sidebar.header("Filters")
departments = sorted(df["Department"].unique())

selected = st.sidebar.multiselect(
    "Select departments",
    departments,
    default=departments,
)

filtered = df[df["Department"].isin(selected)]

if filtered.empty:
    st.warning("Select at least one department.")
    st.stop()

# Summary metrics
c1, c2, c3 = st.columns(3)

c1.metric("Departments", len(filtered))
c2.metric(
    "Average Score",
    f"{filtered['average_score'].mean():.2f}",
)
c3.metric(
    "Average Attendance",
    f"{filtered['average_attendance'].mean():.2f}%",
)

# Charts
left, right = st.columns(2)

with left:
    st.subheader("Average Score by Department")
    fig_score = px.bar(
        filtered,
        x="Department",
        y="average_score",
        color="Department",
        text="average_score",
        title="Department Average Scores",
    )
    st.plotly_chart(fig_score, width="stretch")

with right:
    st.subheader("Average Attendance")
    fig_attendance = px.bar(
        filtered,
        x="Department",
        y="average_attendance",
        color="Department",
        text="average_attendance",
        title="Department Attendance (%)",
    )
    st.plotly_chart(fig_attendance, width="stretch")

st.subheader("Department Summary")
st.dataframe(filtered, width="stretch")

st.download_button(
    "Download Summary CSV",
    data=filtered.to_csv(index=False),
    file_name="department_summary.csv",
    mime="text/csv",
)
# ==========================================
# STUDENT-LEVEL ANALYTICS
# ==========================================

st.divider()
st.header("🎓 Student-Level Analytics")

student_file = BASE_DIR / "data" / "raw" / "students.csv"

if not student_file.exists():
    st.error(f"Student dataset not found: {student_file}")
else:
    student_df = pd.read_csv(student_file)

    # Ensure numeric columns are valid
    student_df["Attendance (%)"] = pd.to_numeric(
        student_df["Attendance (%)"], errors="coerce"
    )
    student_df["Total_Score"] = pd.to_numeric(
        student_df["Total_Score"], errors="coerce"
    )

    student_df = student_df.dropna(
        subset=["Student_ID", "Department", "Attendance (%)",
                "Total_Score", "Grade"]
    )

    # Filters
    f1, f2 = st.columns(2)

    with f1:
        student_departments = st.multiselect(
            "Filter by department",
            sorted(student_df["Department"].unique()),
            default=sorted(student_df["Department"].unique()),
            key="student_departments",
        )

    with f2:
        grades = st.multiselect(
            "Filter by grade",
            sorted(student_df["Grade"].unique()),
            default=sorted(student_df["Grade"].unique()),
            key="student_grades",
        )

    filtered_students = student_df[
        student_df["Department"].isin(student_departments)
        & student_df["Grade"].isin(grades)
    ].copy()

    # Search
    search_id = st.text_input(
        "Search Student ID",
        placeholder="Example: S1000",
        key="student_search",
    )

    if search_id.strip():
        filtered_students = filtered_students[
            filtered_students["Student_ID"]
            .astype(str)
            .str.contains(search_id.strip(), case=False, regex=False)
        ]

    # Metrics
    m1, m2, m3 = st.columns(3)

    m1.metric("Students Selected", len(filtered_students))

    avg_score = (
        filtered_students["Total_Score"].mean()
        if not filtered_students.empty else 0
    )
    m2.metric("Average Total Score", f"{avg_score:.2f}")

    avg_attendance = (
        filtered_students["Attendance (%)"].mean()
        if not filtered_students.empty else 0
    )
    m3.metric("Average Attendance", f"{avg_attendance:.2f}%")

    if filtered_students.empty:
        st.info("No students match the selected filters.")
    else:
        # Grade distribution
        st.subheader("Grade Distribution")

        grade_counts = (
            filtered_students["Grade"]
            .value_counts()
            .rename_axis("Grade")
            .reset_index(name="Students")
        )

        fig_grades = px.bar(
            grade_counts,
            x="Grade",
            y="Students",
            text="Students",
            title="Number of Students by Grade",
        )
        st.plotly_chart(fig_grades, width="stretch")

        # Attendance versus score
        st.subheader("Attendance vs. Total Score")

        fig_scatter = px.scatter(
            filtered_students,
            x="Attendance (%)",
            y="Total_Score",
            color="Grade",
            hover_data=["Student_ID", "Department"],
            title="How Attendance Relates to Student Scores",
        )
        st.plotly_chart(fig_scatter, width="stretch")

        # Student records
        st.subheader("Student Records")

        display_columns = [
            "Student_ID", "Department", "Attendance (%)",
            "Total_Score", "Grade"
        ]

        # Show students with the lowest scores first
        display_students = filtered_students.sort_values(
             by=["Total_Score", "Attendance (%)"],
             ascending=[True, True],
        )
        st.dataframe(
             display_students[display_columns].head(50),
             width="stretch",
             hide_index=True,
        )

        st.download_button(
            "Download Student Records",
            data=filtered_students[display_columns].to_csv(index=False),
            file_name="student_records.csv",
            mime="text/csv",
        )
# ==========================================
# AT-RISK STUDENT IDENTIFICATION
# ==========================================

st.divider()
st.header("⚠️ At-Risk Student Identification")

st.caption(
    "Rule-based screening: students are flagged for review "
    "when attendance is below 60% or total score is below 50."
)

# Adjustable thresholds
col1, col2 = st.columns(2)

with col1:
    attendance_threshold = st.slider(
        "Low attendance threshold (%)",
        min_value=0,
        max_value=100,
        value=60,
        key="risk_attendance_threshold",
    )

with col2:
    score_threshold = st.slider(
        "Low total score threshold",
        min_value=0,
        max_value=100,
        value=50,
        key="risk_score_threshold",
    )

# Create a separate DataFrame; preserve existing data
risk_df = filtered_students.copy()

risk_df["Attendance (%)"] = pd.to_numeric(
    risk_df["Attendance (%)"], errors="coerce"
)
risk_df["Total_Score"] = pd.to_numeric(
    risk_df["Total_Score"], errors="coerce"
)

low_attendance = (
    risk_df["Attendance (%)"] < attendance_threshold
)
low_score = risk_df["Total_Score"] < score_threshold

risk_df["Risk_Reason"] = "No flag"
risk_df.loc[low_attendance, "Risk_Reason"] = "Low attendance"
risk_df.loc[low_score, "Risk_Reason"] = "Low score"
risk_df.loc[
    low_attendance & low_score, "Risk_Reason"
] = "Low attendance + Low score"

risk_df["Risk_Severity"] = "No flag"
risk_df.loc[
    low_attendance | low_score, "Risk_Severity"
] = "Medium priority"
risk_df.loc[
    low_attendance & low_score, "Risk_Severity"
] = "High priority"

# Keep only students who meet at least one rule
at_risk_df = risk_df[
    risk_df["Risk_Reason"] != "No flag"
].copy()

# Summary metrics
m1, m2, m3 = st.columns(3)

m1.metric("Students Flagged", len(at_risk_df))
m2.metric("Students Assessed", len(risk_df))

flagged_percent = (
    len(at_risk_df) / len(risk_df) * 100
    if len(risk_df) > 0 else 0
)
m3.metric("Flagged (%)", f"{flagged_percent:.2f}%")

# Risk severity summary
st.subheader("Risk Severity Summary")

severity_order = [
    "High priority",
    "Medium priority",
    "No flag",
]

severity_df = (
    risk_df["Risk_Severity"]
    .value_counts()
    .reindex(severity_order, fill_value=0)
    .rename_axis("Risk Severity")
    .reset_index(name="Students")
)

st.dataframe(
    severity_df,
    width="stretch",
    hide_index=True,
)
# Visualize risk severity distribution
severity_chart = px.bar(
    severity_df,
    x="Risk Severity",
    y="Students",
    color="Risk Severity",
    text="Students",
    title="Students by Risk Severity",
    category_orders={
        "Risk Severity": [
            "High priority",
            "Medium priority",
            "No flag",
        ]
    },
)

st.plotly_chart(
    severity_chart,
    width="stretch",
)
st.subheader("Flagged Student Records")

risk_columns = [
    "Student_ID",
    "Department",
    "Attendance (%)",
    "Total_Score",
    "Grade",
    "Risk_Reason",
    "Risk_Severity",
]

st.dataframe(
    at_risk_df[risk_columns].sort_values(
        by=["Risk_Severity", "Total_Score"],
        ascending=[True, True],
    ),
    width="stretch",
    hide_index=True,
)

st.download_button(
    "Download At-Risk Student Report",
    data=at_risk_df[risk_columns].to_csv(index=False),
    file_name="at_risk_student_report.csv",
    mime="text/csv",
)
# Student intervention recommendations
st.divider()
st.subheader("🎓 Student Intervention Recommendations")

if at_risk_df.empty:
    st.success("No students currently meet the selected risk rules.")
else:
    intervention_df = at_risk_df.copy()

    intervention_map = {
        "Low attendance": (
            "Review attendance history and discuss barriers "
            "to attending classes."
        ),
        "Low score": (
            "Offer subject-specific tutoring and schedule "
            "a progress review."
        ),
        "Low attendance + Low score": (
            "Arrange an individual academic support meeting "
            "and create a follow-up plan."
        ),
    }

    intervention_df["Recommended_Action"] = (
        intervention_df["Risk_Reason"].map(intervention_map)
    )

    st.caption(
        "Recommendations are rule-based suggestions for educator "
        "review, not definitive assessments of student ability."
    )
    
    # Filter recommendations by risk severity
    severity_options = [
        "High priority",
        "Medium priority",
    ]

    selected_severities = st.multiselect(
        "Filter by risk severity",
        options=severity_options,
        default=severity_options,
        key="intervention_severity_filter",
    )
    metric1, metric2, metric3 = st.columns(3)

    metric1.metric(
        "Students Requiring Intervention",
        len(intervention_df)
    )

    metric2.metric(
        "High Priority",
        int(
            (intervention_df["Risk_Severity"] == "High priority").sum()
        )
    )

    metric3.metric(
        "Medium Priority",
        int(
            (intervention_df["Risk_Severity"] == "Medium priority").sum()
        )
    )
    intervention_df = intervention_df[
        intervention_df["Risk_Severity"].isin(selected_severities)
    ].copy()

    intervention_columns = [
        "Student_ID",
        "Department",
        "Attendance (%)",
        "Total_Score",
        "Risk_Reason",
        "Risk_Severity",
        "Recommended_Action",
    ]

    st.dataframe(
        intervention_df[intervention_columns],
        width="stretch",
        hide_index=True,
    )

    st.download_button(
        "Download Intervention Report",
        data=intervention_df[intervention_columns].to_csv(
            index=False
        ),
        file_name="student_intervention_report.csv",
        mime="text/csv",
    )
