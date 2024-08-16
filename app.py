import streamlit as st
import nltk
import spacy
import pdfplumber
import streamlit as st
import plotly.express as px 
import pandas as pd
import base64, random
import time, datetime
from streamlit_tags import st_tags
from PIL import Image
import pymysql
from Courses import ds_course, web_course, android_course, ios_course, uiux_course, resume_videos, interview_videos
from skill import ds_skills, web_skills, android_skills, ios_skills, uiux_skills
import pafy
import plotly.express as px
import youtube_dl
import re
import streamlit as st
import random
from pytube import YouTube

# Your existing lists of resume and interview videos
resume_videos = [
    "https://youtu.be/c_PZTAW5piQ?si=GCUkxC7iMFwdtPa4",  # Resume Writing: 4 Tips on How to Write a Standout Resume | Indeed Career Tips
    "https://youtu.be/Tt08KmFfIYQ?si=sqfLeljOpZlPpRJH"   # Mastering the Art of Resume Writing: Tips and Tricks
]

interview_videos = [
    "https://youtu.be/EzGH3hZuJVk?si=CknAxycUvHbaUb_Q",  # How to Ace Your Job Interview: The Best Tips
    "https://youtu.be/9bxciZxkTdo?si=QhYQ86CEHY4dFoVh"   # Top Interview Tips: Common Questions and How to Answer Them
]

def fetch_yt_video(url):
    yt = YouTube(url)
    return yt.title

# Download necessary NLTK data
nltk.download('stopwords')

# Load Spacy model
nlp = spacy.load('en_core_web_sm')


def get_table_download_link(df, filename, text):
    """Generates a link allowing the data in a given panda dataframe to be downloaded."""
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()  # some strings <-> bytes conversions necessary here
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">{text}</a>'
    return href

def pdf_reader(file):
    with pdfplumber.open(file) as pdf:
        text = ''
        for page in pdf.pages:
            text += page.extract_text()
    return text

def show_pdf(file_path):
    with open(file_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

def course_recommender(course_list):
    st.subheader("**Courses & Certificates🎓 Recommendations**")
    c = 0
    rec_course = []
    no_of_reco = st.slider('Choose Number of Course Recommendations:', 1, 10, 4)
    random.shuffle(course_list)
    for c_name, c_link in course_list:
        c += 1
        st.markdown(f"({c}) [{c_name}]({c_link})")
        rec_course.append(c_name)
        if c == no_of_reco:
            break
    return rec_course

def calculate_resume_score(resume_text):
    sections = ["projects", "achievements", "hobbies", "certificates", "work experience"]
    score = 0
    for section in sections:
        if re.search(section, resume_text, re.IGNORECASE):
            score += 20
    return score

connection = pymysql.connect(host='localhost', user='root1', password='root')
cursor = connection.cursor()

def insert_data(name, email, res_score, timestamp, no_of_pages, reco_field, cand_level, skills, recommended_skills, courses):
    DB_table_name = 'user_data'
    insert_sql = "insert into " + DB_table_name + """
    values (0,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
    rec_values = (name, email, str(res_score), timestamp, str(no_of_pages), reco_field, cand_level, skills, recommended_skills, courses)
    cursor.execute(insert_sql, rec_values)
    connection.commit()

st.set_page_config(
    page_title="Smart Resume Analyzer",
    page_icon='./Logo/SRA_Logo.ico',
)

def extract_contact_info(resume_text):
    email_pattern = r'[\w\.-]+@[\w\.-]+'
    phone_pattern = r'\+?\d[\d -]{8,}\d'

    email = re.search(email_pattern, resume_text)
    phone = re.search(phone_pattern, resume_text)

    return email.group(0) if email else None, phone.group(0) if phone else None

def run():
    st.title("Smart Resume Analyser")
    st.sidebar.markdown("# Choose User")
    activities = ["Normal User", "Admin"]
    choice = st.sidebar.selectbox("Choose among the given options:", activities)
    link = '[Developed by Pawan](http://github.com/darkx2003)'
    st.sidebar.markdown(link, unsafe_allow_html=True)

    # Create the DB
    db_sql = """CREATE DATABASE IF NOT EXISTS SRA;"""
    cursor.execute(db_sql)
    connection.select_db("sra")

    # Create table
    DB_table_name = 'user_data'
    table_sql = "CREATE TABLE IF NOT EXISTS " + DB_table_name + """
                    (ID INT NOT NULL AUTO_INCREMENT,
                     Name varchar(100) NOT NULL,
                     Email_ID VARCHAR(50) NOT NULL,
                     resume_score VARCHAR(8) NOT NULL,
                     Timestamp VARCHAR(50) NOT NULL,
                     Page_no VARCHAR(5) NOT NULL,
                     Predicted_Field VARCHAR(25) NOT NULL,
                     User_level VARCHAR(30) NOT NULL,
                     Actual_skills VARCHAR(300) NOT NULL,
                     Recommended_skills VARCHAR(300) NOT NULL,
                     Recommended_courses VARCHAR(600) NOT NULL,
                     PRIMARY KEY (ID));
                    """
    cursor.execute(table_sql)

    if choice == 'Normal User':
        pdf_file = st.file_uploader("Choose your Resume", type=["pdf"])
        if pdf_file is not None:
            save_image_path = './Uploaded_Resumes/' + pdf_file.name
            with open(save_image_path, "wb") as f:
                f.write(pdf_file.getbuffer())
            show_pdf(save_image_path)

            # Extract text using pdfplumber
            resume_text = pdf_reader(save_image_path)
            doc = nlp(resume_text)

            # Extract name, email, and phone number from resume text
            resume_data = {'name': None, 'no_of_pages': 0}
            for ent in doc.ents:
                if ent.label_ == 'PERSON' and resume_data['name'] is None:
                    resume_data['name'] = ent.text
            
            # Extract email and phone using regex
            email, phone = extract_contact_info(resume_text)
            
            # Count number of pages
            with pdfplumber.open(save_image_path) as pdf:
                resume_data['no_of_pages'] = len(pdf.pages)

            st.header("**Resume Analysis**")
            st.success("Hello " + resume_data['name'])
            st.subheader("**Your Basic info**")
            st.text('Name: ' + (resume_data['name'] or 'Not Found'))
            st.text('Email: ' + (email or 'Not Found'))
            st.text('Contact: ' + (phone or 'Not Found'))
            st.text('Resume pages: ' + str(resume_data['no_of_pages']))

            cand_level = ''
            if resume_data['no_of_pages'] == 1:
                cand_level = "Fresher"
                st.markdown('''<h4 style='text-align: left; color: #d73b5c;'>You are at Fresher level!.</h4>''', unsafe_allow_html=True)
            elif resume_data['no_of_pages'] == 2:
                cand_level = "Intermediate"
                st.markdown('''<h4 style='text-align: left; color: #1ed760;'>You are at intermediate level!</h4>''', unsafe_allow_html=True)
            elif resume_data['no_of_pages'] >= 3:
                cand_level = "Experienced"
                st.markdown('''<h4 style='text-align: left; color: #fba171;'>You are at experience level!''', unsafe_allow_html=True)

            # st.subheader("**Skills Recommendation💡**")
            # Skills extraction based on predefined skill sets
            found_skills = set()
            recommended_skills = []
            reco_field = ''
            rec_course = ''

            # Match skills with predefined lists
            for word in resume_text.split():
                if word.lower() in ds_skills:
                    found_skills.add(word.lower())
                    reco_field = 'Data Science'
                elif word.lower() in web_skills:
                    found_skills.add(word.lower())
                    reco_field = 'Web Development'
                elif word.lower() in android_skills:
                    found_skills.add(word.lower())
                    reco_field = 'Android Development'
                elif word.lower() in ios_skills:
                    found_skills.add(word.lower())
                    reco_field = 'iOS Development'
                elif word.lower() in uiux_skills:
                    found_skills.add(word.lower())
                    reco_field = 'UI-UX Development'

            # Display extracted and recommended skills
            st.subheader("**Skills Found in Resume 💡**")
            st_tags(label='### Your Skills :', text='See the skills extracted below:', value=list(found_skills))
            
            # Match skills with predefined lists and recommend missing skills
            if reco_field == 'Data Science':
                recommended_skills = list(set(ds_skills) - found_skills)
            elif reco_field == 'Web Development':
                recommended_skills = list(set(web_skills) - found_skills)
            elif reco_field == 'Android Development':
                recommended_skills = list(set(android_skills) - found_skills)
            elif reco_field == 'iOS Development':
                recommended_skills = list(set(ios_skills) - found_skills)
            elif reco_field == 'UI-UX Development':
                recommended_skills = list(set(uiux_skills) - found_skills)

            st.subheader("**Recommended Skills💡:**")
            st_tags(label='', text='Consider adding these skills:', value=recommended_skills)

            # Courses recommendation
            rec_course = []
            if reco_field == 'Data Science':
                rec_course = course_recommender(ds_course)
                st.success("** Our analysis says you are looking for Data Science Jobs **")
            elif reco_field == 'Web Development':
                rec_course = course_recommender(web_course)
                st.success("** Our analysis says you are looking for Web Development Jobs **")
            elif reco_field == 'Android Development':
                rec_course = course_recommender(android_course)
                st.success("** Our analysis says you are looking for Android Development Jobs **")
            elif reco_field == 'iOS Development':
                rec_course = course_recommender(ios_course)
                st.success("** Our analysis says you are looking for iOS Development Jobs **")
            elif reco_field == 'UI-UX Development':
                rec_course = course_recommender(uiux_course)
                st.success("** Our analysis says you are looking for UI-UX Development Jobs **")

            st.subheader("**Resume Tips & Ideas💡**")
            resume_score = 0
            if 'Objective' in resume_text:
                resume_score += 20
                st.markdown(
                    '''<h4 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Objective</h4>''',
                    unsafe_allow_html=True)
            else:
                st.markdown(
                    '''<h4 style='text-align: left; color: #fabc10;'>[-] According to our recommendation please add your career objective, it will give your career intension to the Recruiters.</h4>''',
                    unsafe_allow_html=True)

            if 'Declaration' in resume_text:
                resume_score += 20
                st.markdown(
                    '''<h4 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Declaration✍</h4>''',
                    unsafe_allow_html=True)
            else:
                st.markdown(
                    '''<h4 style='text-align: left; color: #fabc10;'>[-] According to our recommendation please add Declaration✍. It will give the assurance that everything written on your resume is true and fully acknowledged by you</h4>''',
                    unsafe_allow_html=True)

            if 'Hobbies' or 'Interests' in resume_text:
                resume_score += 20
                st.markdown(
                    '''<h4 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Hobbies⚽</h4>''',
                    unsafe_allow_html=True)
            else:
                st.markdown(
                    '''<h4 style='text-align: left; color: #fabc10;'>[-] According to our recommendation please add Hobbies⚽. It will show your personality to the Recruiters and give assurance that you are fit for this role or not.</h4>''',
                    unsafe_allow_html=True)

            if 'Achievements' in resume_text:
                resume_score += 20
                st.markdown(
                    '''<h4 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Achievements🏅</h4>''',
                    unsafe_allow_html=True)
            else:
                st.markdown(
                    '''<h4 style='text-align: left; color: #fabc10;'>[-] According to our recommendation please add Achievements🏅. It will show that you are capable of the required position.</h4>''',
                    unsafe_allow_html=True)

            if 'Projects' in resume_text:
                resume_score += 20
                st.markdown(
                    '''<h4 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Projects👨‍💻</h4>''',
                    unsafe_allow_html=True)
            else:
                st.markdown(
                    '''<h4 style='text-align: left; color: #fabc10;'>[-] According to our recommendation please add Projects👨‍💻. It will show that you have done work related to the required position or not.</h4>''',
                    unsafe_allow_html=True)

            st.subheader("**Resume Score📝**")
            st.markdown(
                """
                <style>
                    .stProgress > div > div > div > div {
                        background-color: #d73b5c;
                    }
                </style>""",
                unsafe_allow_html=True,
            )
            my_bar = st.progress(0)
            score = 0
            for percent_complete in range(resume_score):
                score += 1
                time.sleep(0.1)
                my_bar.progress(percent_complete + 1)
            st.success('** Your Resume Writing Score: ' + str(score) + '**')
            st.warning("** Note: This score is calculated based on the content that you have added in your Resume. **")
            st.balloons()

            # Insert into the database
            insert_data(resume_data['name'], email, str(resume_score), datetime.datetime.now(), str(resume_data['no_of_pages']), reco_field, cand_level, ', '.join(found_skills), ', '.join(recommended_skills), ', '.join(rec_course))

            # Resume Writing Video Recommendations
            st.header("**Bonus Video for Resume Writing Tips 💡**")
            resume_vid = random.choice(resume_videos)
            res_vid_title = fetch_yt_video(resume_vid)
            st.subheader("✅ **" + res_vid_title + "**")
            st.video(resume_vid)

            # Interview Preparation Video Recommendations
            st.header("**Bonus Video for Interview 👨‍💼 Tips 💡**")
            interview_vid = random.choice(interview_videos)
            int_vid_title = fetch_yt_video(interview_vid)
            st.subheader("✅ **" + int_vid_title + "**")
            st.video(interview_vid)

            st.snow()

            connection.commit()

    elif choice == 'Admin':
        ## Admin Side
        st.success('Welcome to Admin Side')
        # st.sidebar.subheader('**ID / Password Required!**')

        ad_user = st.text_input("Username")
        ad_password = st.text_input("Password", type='password')
        if st.button('Login'):
            if ad_user == 'pawan' and ad_password == 'pawan':
                st.success("Welcome Pawan :) ")
                # Display Data
                cursor.execute('''SELECT*FROM user_data''')
                data = cursor.fetchall()
                st.header("**User's👨‍💻 Data**")
                df = pd.DataFrame(data, columns=['ID', 'Name', 'Email', 'Resume Score', 'Timestamp', 'Total Page',
                                                 'Predicted Field', 'User Level', 'Actual Skills', 'Recommended Skills',
                                                 'Recommended Course'])
                st.dataframe(df)
                st.markdown(get_table_download_link(df, 'User_Data.csv', 'Download Report'), unsafe_allow_html=True)
                ## Admin Side Data
                query = 'select * from user_data;'
                plot_data = pd.read_sql(query, connection)

                # Pie chart for Predicted Field Recommendations
                st.subheader("📈 **Pie-Chart for Predicted Field Recommendations**")
                predicted_field_counts = plot_data['Predicted_Field'].value_counts().reset_index()
                predicted_field_counts.columns = ['Predicted_Field', 'Count']
                fig = px.pie(predicted_field_counts, values='Count', names='Predicted_Field', title='Predicted Field according to the Skills')
                st.plotly_chart(fig)

                # Pie chart for User's Experienced Level
                st.subheader("📈 **Pie-Chart for User's👨‍💻 Experienced Level**")
                user_level_counts = plot_data['User_level'].value_counts().reset_index()
                user_level_counts.columns = ['User_level', 'Count']
                fig = px.pie(user_level_counts, values='Count', names='User_level', title="Pie-Chart📈 for User's👨‍💻 Experienced Level")
                st.plotly_chart(fig)


            else:
                st.error("Wrong ID & Password Provided")


run()
