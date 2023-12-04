import streamlit as st
import plotly.express as px
import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
import time, requests
import action, gamelog as GL, trends # Sections of the app

def fix_dates(df):
    '''
    Pass in 'gamelog'. This will fix the dates and make them usable for plotting.
    '''
    ## fixing date column...
    df['DATE'] = df['DATE'].str[4:]

    year = time.strftime("%Y")

    date_df = df['DATE'].str.split(expand=True)
    date_df.rename(columns={0:'month',1:'day'}, inplace=True)
    date_df['year'] = year
    date_df['full'] = date_df['month'] + ' ' + date_df['day'] + ', ' + date_df['year']
    date_df['DATE'] = pd.to_datetime(date_df['full'])

    df['DATE'] = date_df['DATE']
    return df

def get_today_slate():
    url = 'https://www.espn.com/nba/lines'
    r = requests.get(url)
    soup = BeautifulSoup(r.content, 'html.parser')
    parsed = soup.find_all('tr')

    names, records, mls = [], [], []
    for game in parsed:
        try:
            name = game.find_all('td')[0].get_text()
            record = game.find_all('td')[1].get_text()[0:5]
            ml = game.find_all('td')[3].get_text()

            names.append(name)
            records.append(record)
            mls.append(ml)
        except: pass

    i=0
    home, away, homerec, awayrec, homeml, awayml = [], [], [], [], [], []
    for name, record, ml in zip(names, records, mls):
        i=i+1
        if i % 2 == 0:
            home.append(name)
            homerec.append(record)
            homeml.append(ml)
        else:
            away.append(name)
            awayrec.append(record)
            awayml.append(ml)

    return pd.DataFrame({'away':away,'home':home, 'awayrec':awayrec, 'homerec':homerec, 'awayml':awayml, 'homeml':homeml})

def gen_plotly(log, stat):
    '''
    Input: 'stat' is 'PTS','REB','AST','3PM','PRA'
    -If any player is chosen, subset to only that player's trends
    -x axis Dates, y axis is stat of choice
    '''
    color_dict = {'PTS':'#E41A1C', 'REB':'#3773B8', 'AST':'#4DAF4A', '3PM':'#FF7F00','PRA':'#984EA3'}
    name_dict = {'PTS':'Points', 'REB':'Rebounds', 'AST':'Assists','3PM':'Threes','PRA':'Pts/Reb/Ast'}

    fig = px.line(x = log['DATE'], y = log[stat], title=player_subset, labels={'x':'Date','y':name_dict[stat]})
    fig['data'][0]['showlegend']=True
    fig['data'][0]['name']=name_dict[stat]
    fig['data'][0]['line']['color']=color_dict[stat]
    fig.update_layout(hovermode='x unified')
    st.plotly_chart(fig, use_container_width=True)

## set equivalencies for team / full name
team_dict = {'ATL':'Hawks', 'BKN':'Nets', 'BOS':'Celtics', 'CHA':'Hornets', 'CHI':'Bulls', 'CLE':'Cavaliers', 'DAL':'Mavericks','DEN':'Nuggets','DET':'Pistons','GSW':'Warriors','HOU':'Rockets','IND':'Pacers','LAC':'Clippers','LAL':'Lakers','MEM':'Grizzlies','MIA':'Heat','MIL':'Bucks','MIN':'Timberwolves','NOR':'Pelicans','NYK':'Knicks','OKC':'Thunder','ORL':'Magic','PHI':'76ers','PHO':'Suns','POR':'Trail Blazers','SAC':'Kings','SAS':'Spurs','TOR':'Raptors','UTH':'Jazz','WAS':'Wizards'}

st.set_page_config(page_title='PROPZ v4.0.0', page_icon=':basketball:', layout="wide", initial_sidebar_state="auto", menu_items=None)
hide_menu_style = """
        <style>
        #MainMenu {visibility: hidden;}
        </style>
        """
st.markdown(hide_menu_style, unsafe_allow_html=True)

## load the gamelog
gamelog = pd.read_csv('gamelog.csv')
gamelog = fix_dates(gamelog)
gamelog['HOME/AWAY'] = np.where(gamelog['OPP'].str.contains('@'), 'AWAY', 'HOME')

st.markdown("<h1 style='text-align: center;'>NBA PROPZ 4.0.0</h1>", unsafe_allow_html=True)

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

st.markdown("<h2 style='text-align: center;'>Upcoming Matchups</h2>", unsafe_allow_html=True)
today = get_today_slate()

st.markdown("<h6 style='text-align:center;'>(ML) (Record) Away Team @ Home Team (Record) (ML)", unsafe_allow_html=True)
for i, row in today.iterrows():
    st.markdown("<h6 style='text-align: center;'>({}) ({}) {} @ {} ({}) ({})".format(row.awayml, row.awayrec, row.away, row.home, row.homerec, row.homeml), unsafe_allow_html=True)


## @TODO:
#st.header("Suggested Props for Today's Slate")
#st.write('Coming soon')

c1, _ = st.columns(2)
with c1:
    if player_subset!='Choose Player':
        plotbox = st.sidebar.selectbox(label='Show Plots', options=['All Stats','Points','Rebounds','Assists','Threes','Pts/Reb/Ast'])

try:
    playerlog = gamelog[gamelog['NAME']==player_subset].sort_values(by='DATE')
    if plotbox=='All Stats':
        fig = px.line(x = playerlog['DATE'], y = playerlog['PTS'], title=player_subset,labels={'x':'Date', 'y':''})
        fig['data'][0]['showlegend']=True
        fig['data'][0]['name']='Points'
        fig['data'][0]['line']['color']='#E41A1C'
        fig.add_scatter(x = playerlog['DATE'], y = playerlog['REB'], name='Rebounds', line_color='#3773B8')
        fig.add_scatter(x = playerlog['DATE'], y = playerlog['AST'], name='Assists', line_color='#4DAF4A')
        fig.add_scatter(x = playerlog['DATE'], y = playerlog['3PM'], name='Threes', line_color='#FF7F00')
        fig.add_scatter(x = playerlog['DATE'], y = playerlog['PRA'], name='PRA', line_color='#984EA3')
        fig.update_layout(hovermode='x unified')
        st.plotly_chart(fig, use_container_width=True)
    if plotbox=='Points': gen_plotly(playerlog, 'PTS')
    if plotbox=='Rebounds': gen_plotly(playerlog, 'REB')
    if plotbox=='Assists': gen_plotly(playerlog, 'AST')
    if plotbox=='Threes': gen_plotly(playerlog, '3PM')
    if plotbox=='Pts/Reb/Ast': gen_plotly(playerlog, 'PRA')
except: pass   

## Action Network Section
thres = {'pts':19.5,'reb':5.5,'ast':3.5,'3pm':1.5,'pra':24.5}
action.displayActionNetworkSection(thres, team_subset, player_subset, team_dict)

## PROP SLIDERS
## if player is in the action data, set the default value to their current line based on selected book
## otherwise, default is used

thres_pts = st.sidebar.number_input('Points', value=thres['pts'], step=1.0, help='Adjust threshold for points to compare prop trends.', format='%f')
thres_reb = st.sidebar.number_input('Rebounds', value=thres['reb'], step=1.0, help='Adjust threshold for rebounds to compare prop trends.', format='%f')
thres_ast = st.sidebar.number_input('Assists', value=thres['ast'], step=1.0, help='Adjust threshold for assists to compare prop trends.', format='%f')
thres_3pm = st.sidebar.number_input('Threes', value=thres['3pm'], step=1.0, help='Adjust threshold for threes to compare prop trends.', format='%f')
thres_pra = st.sidebar.number_input('Pts/Reb/Ast', value=thres['pra'], step=1.0, help='Adjust threshold for PRA to compare prop trends.', format='%f')

## TRENDS SECTION
trends.displayPlayerTrends(gamelog, player_subset, thres_pts, thres_reb, thres_ast, thres_3pm, thres_pra)

GL.displayGameLog(gamelog, team_subset, player_subset)