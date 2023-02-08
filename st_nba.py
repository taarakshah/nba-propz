import streamlit as st
import plotly.express as px
import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time

def fix_dates(df):
    '''
    Pass in 'gamelog'. This will fix the dates and make them usable for plotting.
    '''
    ## fixing date column...
    df['DATE'] = df['DATE'].str[4:]

    ## append 2022 or 2023 to DATE
    months22 = ['Oct', 'Nov', 'Dec']

    date_df = df['DATE'].str.split(expand=True)
    date_df.rename(columns={0:'month',1:'day'}, inplace=True)
    date_df['year'] = np.where(date_df['month'].isin(months22), '2022', '2023')
    date_df['full'] = date_df['month'] + ' ' + date_df['day'] + ', ' + date_df['year']
    date_df['DATE'] = pd.to_datetime(date_df['full'])

    df['DATE'] = date_df['DATE']
    return df

def get_new_data():
    '''
    Gets new NBA player prop data from FantasyPros. Returns a dataframe of all players above 25 mpg.
    '''

    ## First get all players who average more than 25 mpg
    url = 'https://www.fantasypros.com/nba/stats/avg-overall.php'
    r = requests.get(url)
    soup = BeautifulSoup(r.content, 'html.parser')
    parsed = soup.find_all('tr')
    ## parsed[0] has the main table with all the player averages
    ## info needed: player name (+href), min per game

    names, teams, hrefs, mpgs = [], [], [], []

    for player in parsed:
        try:
            ## find player name / link to player
            name = player.find_all('td')[0].find('a').get_text()
            href = player.find_all('td')[0].find('a').get('href')
            ## get player min/game
            mpg = float(player.find_all('td')[11].get_text())
            ## get player team
            team = player.find_all('td')[0].find('small').get_text()[1:4]

            ## save all to list
            names.append(name)
            teams.append(team)
            hrefs.append(href)
            mpgs.append(mpg)
        except: pass

    ## make it a dataframe
    players = pd.DataFrame(list(zip(names, teams, hrefs, mpgs)), columns=['name','team', 'href','mpg'])

    players25 = players[players['mpg'] >= 25.0].sort_values(by='team').reset_index(drop=True)
    ## split the .php ending for each player to get game log links..need it like trae-young.php, luka-doncic.php, etc
    phplist = []
    for i in range(len(players25.href)):
        php = players25['href'].str.split('/')[i][3]
        phplist.append(php)
    ## add it to df
    players25['php'] = phplist
    players = players25.drop(['href','mpg'], axis=1)

    ## Get the URL and HTML content of the game log page
    urlbuild = 'https://www.fantasypros.com/nba/games/' ## need to + the "php" column for each player from previous dataframe, done in loop
    gamelog = pd.DataFrame()
    for i in range(len(players.php)):
        ## build URL to pull gamelog from
        url = urlbuild + players['php'][i]
        r = requests.get(url)
        soup = BeautifulSoup(r.content, 'html.parser')
        parsed = soup.find_all('tr')
        ## lists per player
        dates, mins, fgms, fgas, tpms, tpas, ftms, ftas, rebs, asts, tos, stls, blks, pfs, pts, pras = [],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]

        for game in parsed:
            try:
                date = game.find_all('td')[0].get_text()
                min = int(game.find_all('td')[3].get_text())
                fgm = int(game.find_all('td')[4].get_text())
                fga = int(game.find_all('td')[5].get_text())
                tpm = int(game.find_all('td')[7].get_text())
                tpa = int(game.find_all('td')[8].get_text())
                ftm = int(game.find_all('td')[10].get_text())
                fta = int(game.find_all('td')[11].get_text())
                reb = int(game.find_all('td')[15].get_text())
                ast = int(game.find_all('td')[16].get_text())
                to = int(game.find_all('td')[17].get_text())
                stl = int(game.find_all('td')[18].get_text())
                blk = int(game.find_all('td')[19].get_text())
                pf = int(game.find_all('td')[20].get_text())
                pt = int(game.find_all('td')[21].get_text())
                pra = pt+reb+ast
                ## save all to list
                dates.append(date)
                mins.append(min)
                fgms.append(fgm)
                fgas.append(fga)
                tpms.append(tpm)
                tpas.append(tpa)
                ftms.append(ftm)
                ftas.append(fta)
                rebs.append(reb)
                asts.append(ast)
                tos.append(to)
                stls.append(stl)
                blks.append(blk)
                pfs.append(pf)
                pts.append(pt)
                pras.append(pra)
            except: pass

            ## make it a dataframe
            minilog = pd.DataFrame(list(zip(dates, mins, fgms, fgas, tpms, tpas, ftms, ftas, rebs, asts, tos, stls, blks, pfs, pts, pras)),
                                columns=['DATE','MIN','FGM','FGA','3PM','3PA','FTM','FTA','REB','AST','TO','STL','BLK','PF','PTS','PRA'])
        player_name = players['name'][i]
        player_team = players['team'][i]
        minilog['NAME'] = player_name
        minilog['TEAM'] = player_team
        
        ## combine all player gamelogs
        gamelog = pd.concat([gamelog, minilog], ignore_index=False)

    gamelog = fix_dates(gamelog)
    return gamelog

st.set_page_config(page_title='PROPZ v2.1.0', page_icon=':basketball:', layout="wide", initial_sidebar_state="auto", menu_items=None)

c1, c2 = st.columns(2)
with c2:
    ## Button for getting new data from FantasyPros
    newdata = st.button('Gather new NBA player prop data', help='Gets new NBA player prop data from FantasyPros. Returns data of all players above 25 min/game.')
    if newdata:
        start = time.time()
        gamelog = get_new_data()
        end = time.time()
        st.write('New game log took {} seconds to gather.'.format( np.round(end-start,1) ) )
    else:
        ## read in default gamelog
        gamelog = pd.read_csv('gamelog.csv')
        gamelog = fix_dates(gamelog)
with c1:
    if newdata:
        st.write('Game log is current as of today.')
    else:
        st.write('Game log is current as of Feb 6, 2023.')
        st.write('Check the box to refresh. Will take approx ~90 seconds.')


st.markdown("<h1 style='text-align: center;'>NBA PROPZ 2.1.0</h1>", unsafe_allow_html=True)
hide_menu_style = """
        <style>
        #MainMenu {visibility: hidden;}
        </style>
        """
st.markdown(hide_menu_style, unsafe_allow_html=True)

def convert_df(df):
   return df.to_csv(index=False).encode('utf-8')


## SIDEBAR / OPTIONS MENU
st.sidebar.markdown("## Options Menu")

## get unique teams
teams_list = gamelog['TEAM'].unique().tolist()
## team option
team_subset = st.sidebar.selectbox('Team', options=['Choose Team'] + teams_list)

## if a team is chosen, only show players from that team
if team_subset=='Choose Team':
    player_list = gamelog['NAME'].unique().tolist()
else:
    player_list = gamelog[gamelog['TEAM']==team_subset]['NAME'].unique().tolist()
## player option
player_subset = st.sidebar.selectbox('Player', options=['Choose Player'] + player_list)

## prop sliders
thres_pts = st.sidebar.number_input('Points', value=19.5, step=1.0, help='Adjust threshold for points to compare prop trends.')
thres_reb = st.sidebar.number_input('Rebounds', value=5.5, step=1.0, help='Adjust threshold for rebounds to compare prop trends.')
thres_ast = st.sidebar.number_input('Assists', value=3.5, step=1.0, help='Adjust threshold for assists to compare prop trends.')
thres_3pm = st.sidebar.number_input('Threes', value=1.5, step=1.0, help='Adjust threshold for threes to compare prop trends.')
thres_pra = st.sidebar.number_input('Pts/Reb/Ast', value=24.5, step=1.0, help='Adjust threshold for PRA to compare prop trends.')


st.header('Show Plots Over Time')
c1,c2,c3,c4,c5 = st.columns(5)
with c1: plot_pts = st.button('Points')
with c2: plot_reb = st.button('Rebounds')
with c3: plot_ast = st.button('Assists')
with c4: plot_3pm = st.button('Threes')
with c5: plot_pra = st.button('Pts/Reb/Ast')


## Print trends
if player_subset!='Choose Player':
    st.header('{} has hit...'.format(player_subset))
    l5 = gamelog[gamelog['NAME']==player_subset].head(5)
    l10 = gamelog[gamelog['NAME']==player_subset].head(10)
    l25 = gamelog[gamelog['NAME']==player_subset].head(25)

    st.write('...over {} points in {}/5, {}/10, and {}/25'.format(thres_pts, sum(l5['PTS'] >= thres_pts), sum(l10['PTS'] >= thres_pts), sum(l25['PTS'] >= thres_pts) ) )
    st.write('...over {} rebounds in {}/5, {}/10, and {}/25'.format(thres_reb, sum(l5['REB'] >= thres_reb), sum(l10['REB'] >= thres_reb), sum(l25['REB'] >= thres_reb) ) )
    st.write('...over {} assists in {}/5, {}/10, and {}/25'.format(thres_ast, sum(l5['AST'] >= thres_ast), sum(l10['AST'] >= thres_ast), sum(l25['AST'] >= thres_ast) ) )
    st.write('...over {} threes in {}/5, {}/10, and {}/25'.format(thres_3pm, sum(l5['3PM'] >= thres_3pm), sum(l10['3PM'] >= thres_3pm), sum(l25['3PM'] >= thres_3pm) ) )
    st.write('...over {} PRA in {}/5, {}/10, and {}/25'.format(thres_pra, sum(l5['PRA'] >= thres_pra), sum(l10['PRA'] >= thres_pra), sum(l25['PRA'] >= thres_pra) ) )

## Associated detailed data / descriptions
st.header('Full Game Log for Chosen Player')
st.write('If a player is chosen with the filter menu on the left, it will show the game log of that player. Otherwise, it will show the full game log for all possible players and teams.')

## Consider all cases for displaying data
## Do not choose team or player -> show full log
if (team_subset=='Choose Team') & (player_subset=='Choose Player'):
    st.dataframe(gamelog)
## Choose team but not a player -> show log for all players on chosen team
elif (team_subset!='Choose Team') & (player_subset=='Choose Player'):
    st.dataframe(gamelog[gamelog.TEAM==team_subset].reset_index(drop=True))
## Choose player -> show log for chosen player
elif player_subset!='Choose Player':
    st.dataframe(gamelog[gamelog.NAME==player_subset].reset_index(drop=True))

## Button for downloading gamelog data to CSV
gamelog_csv = convert_df(gamelog)
st.download_button("Download CSV of full game log for all players", gamelog_csv, "gamelog.csv", "text/csv", key='download-csv')