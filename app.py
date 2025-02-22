from flask import Flask, url_for, redirect, render_template, request, jsonify, make_response
import sqlite3
import datetime
import pandas as pd
import os
from module.logger import Logger
from urllib.parse import unquote

app = Flask(__name__)
logger = Logger(__name__)
DEBUG = True

ADMIN_PASS = "FYPDP2025_admin135"

def init_database() -> None:
    """
    Initializes the poll database by creating a table if it does not exist.

    The table has the following columns:
        id: The unique identifier for the poll entry.
        criteria: The criteria for which the user voted.
        study: The study for which the user voted.
        ip_address: The IP address of the user.

    Note that this function does not have any parameters or return values.
    """
    logger.log("info", "Initialising database...")
    conn = sqlite3.connect('poll.db')
    cursor = conn.cursor()

    #Create a table if exists
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS poll(
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   criteria TEXT NOT NULL,
                   study TEXT NOT NULL,
                   ip_address TEXT NOT NULL)
                   """)
    conn.commit()
    conn.close()
    logger.log("info", "Database has been initialised on {}.".format(datetime.datetime.now()))


def get_ip() -> str:
    #IP Address
    """
    Retrieves the IP address of the user. If the app is behind a proxy,
    it will check the 'X-Forwarded-For' header and return the first address
    in the list. Otherwise, it will return the REMOTE_ADDR value.

    Returns:
        str: IP address of the user
    """
    ip_address = request.remote_addr

    # If your app is behind a proxy, you might check 'X-Forwarded-For'
    if request.headers.get('X-Forwarded-For'):
        ip_address = request.headers.get('X-Forwarded-For').split(',')[0].strip()
    
    return ip_address

@app.route("/vote/<study>")
def vote(study):
    """
    This function handles the voting process. It will check if the IP address
    has already voted. If not, it will add the vote to the database, and set a
    cookie to indicate that the user has already voted.

    Parameters:
    study (str): The study to vote for, in the format "category-study"
    """
    #init database if not made
    if 'poll.db' not in os.listdir():
        init_database()

    #Check if ip_address is already inside the 
    ip_address = get_ip()

    conn = sqlite3.connect('poll.db')
    cursor = conn.cursor()

    cursor.execute("SELECT ip_address FROM poll")
    results = [i[0] for i in cursor.fetchall()]
    conn.close()

    ip_is_voted = ip_address in results


    #Check if they have already voted using the cookie
    if request.headers.get('X-Forwarded-For'):
        ip_address = request.headers.get('X-Forwarded-For').split(',')[0].strip()


    if request.cookies.get('has_voted'):
        cookie_is_voted = True
    else:
        response = make_response(jsonify({"message": "Your vote has been recorded"}))
        response.set_cookie('has_voted', 'true', max_age=60 * 60 * 24 * 7)  #Max Age is 1 week.
        cookie_is_voted = False
    
    #Get the category and study from the study database
    conn = sqlite3.connect('study.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM studies WHERE ID = ?", (study,))
    results = cursor.fetchall()
    conn.close()

    #This should only have one result
    category = results[0][0]
    study_title = results[0][1]

    #Add to the database if no cookie is present and ip not found in db
    if ((ip_is_voted == False) and (cookie_is_voted == False)) or DEBUG:
        conn = sqlite3.connect('poll.db')
        cursor = conn.cursor()
        cursor.execute("""
                INSERT INTO poll (criteria, study, ip_address)
                VALUES (?, ?, ?)
            """, (category, study_title, ip_address))
        conn.commit()
        #Add the log
        logger.log("info", "Inserted the values at {}\n{}\t{}\t{}".format(datetime.datetime.now(),category, study_title, ip_address))
        
        conn.close()
        return render_template(r'base/voted.html',category = category, study_title = study_title, ip_address = ip_address)

    else:
        print('User has already voted')
        return render_template(r'base/error.html', message="You have already voted. If you believe this is an error, please contact the FYPDP team.")


@app.route("/livepoll")
def live_poll():
    """
    Handles the live poll display by fetching and aggregating poll data 
    from the database, and rendering it on the live poll page.

    The function connects to the 'poll.db' SQLite database, retrieves the
    count of votes grouped by criteria and study, and organizes the data
    into a DataFrame. The data is then aggregated by category, sorted by 
    the number of votes, and passed to the 'livepoll.html' template for 
    rendering.

    Returns:
        Rendered template for the live poll page with aggregated data.
    """
    #init database if not made
    if 'poll.db' not in os.listdir():
        return render_template(r'base/error.html', message="No votes found.If you believe this is an error, please contact the FYPDP team.")
    
    #Get the data from the database
    conn = sqlite3.connect('poll.db')
    cursor = conn.cursor()

    cursor.execute("""
        SELECT criteria, study, COUNT(*) as votes
        FROM poll
        GROUP BY criteria, study;
        """)
    
    results = cursor.fetchall()
    conn.close()

    df = pd.DataFrame(results, columns=['Category', 'Study', 'Votes'])
    aggregated = [i.sort_values(by='Votes').values.tolist() for idx, i in df.groupby('Category')]
    
    print(aggregated)
    return render_template('base/livepoll.html', aggregated = aggregated)

@app.route("/admin", methods=["GET","POST"])
def admin_post():
    """ Handle the admin reset database functionality.
        
        If the request is POST and contains the "reset_database" key, 
        then check if the user has confirmed the reset. If so, remove the 
        database file and reinitialise it, then return a success message.
    """
    
    if request.method == "POST":
        print("Post Received")
        print(request.form)
        if request.form.get("confirm_reset") == "true":
            print("Confirmed")
            os.remove("poll.db")
            logger.log("warning", "Database has been deleted.")
            init_database()
            logger.log("info", "Database has been reinitialised.")

            return redirect(url_for("admin_post"))  

    return render_template("base/admin.html", password = ADMIN_PASS)

@app.errorhandler(404)
def page_not_found(error):
    return render_template('base/error.html', message="Page not found. If you believe this is an error, please contact the FYPDP team. "), 404