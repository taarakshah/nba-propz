import streamlit as st
import plotly.express as px
import numpy as np
import pandas as pd
import requests
import bs4
from bs4 import BeautifulSoup
import time
import json

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

def action_scrape(sport=None, propnames=None):
    fulldf = pd.DataFrame()
    ## need header for access to site
    headers = {'User-Agent': 'Mozilla/5.0'}
    for propname in propnames:
        urlbuild = 'https://www.actionnetwork.com/'+sport+'/props/'
        url = urlbuild + propname
        r = requests.get(url, headers=headers)
        soup = BeautifulSoup(r.content, 'html.parser')
        ## get json
        parsed = soup.find_all('script')
        jstext = parsed[-1].string
        ## load entire json into pandas, drop unnecessary columns
        data = json.loads(jstext)
        #print( json.dumps(data, indent=2) )
        df_js = pd.json_normalize(data)

        ## get o/u corresponding value -- smaller corresponds to over, larger corresponds to under according to nba
        ## checker:
        #print(df_js.filter(regex='props.pageProps.initialMarketConfig.market.rules.options'))
        cols = df_js.filter(regex='props.pageProps.initialMarketConfig.market.rules.options').columns.tolist()
        ## remove prefix string, keep only the number, and save it to unique list to avoid dupes
        try:
            nums = []
            for i in range(len(cols)):
                nums.append(int(cols[i].replace('props.pageProps.initialMarketConfig.market.rules.options.', '')[0:2].replace('.','')))
                nums = np.unique(nums).tolist()
        except: pass

        ## get name of prop page
        stat = df_js['props.pageProps.SEOData.header'].values[0]

        ## keep relevant columns now that we have o/u numbers, expand the json
        keep = 'props.pageProps.initialMarketConfig.market.'
        cols_to_keep = [keep+'books',keep+'teams',keep+'players']
        df = df_js[cols_to_keep]
        df = df.copy()
        df.rename(columns={cols_to_keep[0]:'books', cols_to_keep[1]:'teams', cols_to_keep[2]:'players'}, inplace=True)

        ## create odds df
        odds = pd.json_normalize(df['books'][0], record_path='odds', meta='book_id')
        odds = odds[odds.columns.drop(list(odds.filter(regex='deeplink')))]
        # create o/u to be obvious -- its hidden in option type id -- smaller num corresponds to over, larger to under
        try:
            odds['ou'] = np.where(odds['option_type_id']==np.min(nums), 'over', 'under')
        except: pass

        ## get book names
        book_ids = odds.book_id.unique()
        bookdict= {}
        for i in book_ids:
            try:
                book = df_js['props.pageProps.bookMap.{}.display_name'.format(i)].values[0]
                if i not in bookdict:
                    bookdict[i] = book
            except: pass
        ## exception for other book id
        bookdict[15] = 'Best Odds'

        teams = pd.json_normalize(df['teams'][0])
        players = pd.json_normalize(df['players'][0])
        books = pd.DataFrame(bookdict.items(), columns=['book_id', 'book_name'])

        odds1 = odds.merge(books, on='book_id')
        odds2 = odds1.merge(teams[['id','display_name']], left_on='team_id', right_on='id')
        odds3 = odds2.merge(players[['id','full_name']], left_on='player_id', right_on='id')
        df = odds3[odds3.columns.drop(list(odds.filter(regex='id')))]
        df = df.drop(['id_x','id_y'], axis=1)
        df['prop'] = propname
        df = df.sort_values(by=['prop','full_name','book_name','is_best'], ascending=[True,True,True,False])
        fulldf = pd.concat([fulldf, df], ignore_index=True)
    return fulldf

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
def convert_df(df):
    return df.to_csv(index=False).encode('utf-8')

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

## get action data for NBA props
nba_propnames = ['points', 'rebounds', 'assists', '3fgm', 'points-rebounds-assists']
name_dict = {'points':''}
action = action_scrape(sport='nba', propnames=nba_propnames)
action_display = action[['edge','prop','ou','value','money','full_name','display_name','grade','implied_value','projected_value','bet_quality','book_name',]]

st.subheader('Action Edge Data')

c1, c2 = st.columns(2)
with c1:
    st.write('Below is data from Action Network on player edges and lines across books. Choose your book, or "all", to update the data. Choosing a specific team or player will also update the data to only show that team or player. If a team is not playing today, the data will come up empty. Click on a column to sort by that column.')
with c2:
    book_opt = st.selectbox('Select Book', options=['All'] + action['book_name'].unique().tolist()[1:])

### cases to display
## set thresholds, update them if certain player is chosen in action data
thres = {'pts':19.5,'reb':5.5,'ast':3.5,'3pm':1.5,'pra':24.5}
## all books, all teams, all players
if (book_opt=='All') & (team_subset=='Choose Team') & (player_subset=='Choose Player'):
    ## all books, all teams, all players
    st.dataframe(action_display)
## all books, certain team, all players
elif (book_opt=='All') & (team_subset!='Choose Team') & (player_subset=='Choose Player'):
    st.dataframe(action_display[action_display['display_name']==team_dict[team_subset]])
## all books, certain player ################################################################## UPDATES THRESHOLDS
elif (book_opt=='All') & (player_subset!='Choose Player'):
    temp = action_display[action_display['full_name']==player_subset]
    st.dataframe(temp)

    try:
        thres['pts'] = temp[temp['prop']=='points']['value'].values[0]
        thres['reb'] = temp[temp['prop']=='rebounds']['value'].values[0]
        thres['ast'] = temp[temp['prop']=='assists']['value'].values[0]
        thres['3pm'] = temp[temp['prop']=='3fgm']['value'].values[0]
        thres['pra'] = temp[temp['prop']=='points-rebounds-assists']['value'].values[0]
    except: pass
## certain book, all teams, all players
elif (book_opt!='All') & (team_subset=='Choose Team') & (player_subset=='Choose Player'):
    st.dataframe(action_display[action_display['book_name']==book_opt])
## certain book, certain team, all players
elif (book_opt!='All') & (team_subset!='Choose Team') & (player_subset=='Choose Player'):
    st.dataframe(action_display[ (action_display['book_name']==book_opt) & (action_display['display_name']==team_dict[team_subset])])
## certain book, certain player ############################################################## UPDATES THRESHOLDS
elif (book_opt!='All') & (player_subset!='Choose Player'):
    temp = action_display[ (action_display['book_name']==book_opt) & (action_display['full_name']==player_subset) ]
    st.dataframe(temp)

    try:
        thres['pts'] = temp[temp['prop']=='points']['value'].values[0]
        thres['reb'] = temp[temp['prop']=='rebounds']['value'].values[0]
        thres['ast'] = temp[temp['prop']=='assists']['value'].values[0]
        thres['3pm'] = temp[temp['prop']=='3fgm']['value'].values[0]
        thres['pra'] = temp[temp['prop']=='points-rebounds-assists']['value'].values[0]
    except: pass
else:
    st.write('What fuckin option combo is this? Anyway, something is wrong, here is the full data.')
    st.dataframe(action_display)
    

## PROP SLIDERS
## if player is in the action data, set the default value to their current line based on selected book
## otherwise, default is used

thres_pts = st.sidebar.number_input('Points', value=thres['pts'], step=1.0, help='Adjust threshold for points to compare prop trends.', format='%f')
thres_reb = st.sidebar.number_input('Rebounds', value=thres['reb'], step=1.0, help='Adjust threshold for rebounds to compare prop trends.', format='%f')
thres_ast = st.sidebar.number_input('Assists', value=thres['ast'], step=1.0, help='Adjust threshold for assists to compare prop trends.', format='%f')
thres_3pm = st.sidebar.number_input('Threes', value=thres['3pm'], step=1.0, help='Adjust threshold for threes to compare prop trends.', format='%f')
thres_pra = st.sidebar.number_input('Pts/Reb/Ast', value=thres['pra'], step=1.0, help='Adjust threshold for PRA to compare prop trends.', format='%f')

## Print trends
if player_subset != 'Choose Player':
    st.header('{} has hit...'.format(player_subset))
    c1,c2,c3 = st.columns(3)
    with c1:
        st.subheader('...in all games:')
        l5 = gamelog[gamelog['NAME']==player_subset].head(5)
        l10 = gamelog[gamelog['NAME']==player_subset].head(10)
        l25 = gamelog[gamelog['NAME']==player_subset].head(25)

        st.write('...over {} points in {}/5, {}/10, and {}/25'.format(thres_pts, sum(l5['PTS'] >= thres_pts), sum(l10['PTS'] >= thres_pts), sum(l25['PTS'] >= thres_pts) ) )
        st.write('...over {} rebounds in {}/5, {}/10, and {}/25'.format(thres_reb, sum(l5['REB'] >= thres_reb), sum(l10['REB'] >= thres_reb), sum(l25['REB'] >= thres_reb) ) )
        st.write('...over {} assists in {}/5, {}/10, and {}/25'.format(thres_ast, sum(l5['AST'] >= thres_ast), sum(l10['AST'] >= thres_ast), sum(l25['AST'] >= thres_ast) ) )
        st.write('...over {} threes in {}/5, {}/10, and {}/25'.format(thres_3pm, sum(l5['3PM'] >= thres_3pm), sum(l10['3PM'] >= thres_3pm), sum(l25['3PM'] >= thres_3pm) ) )
        st.write('...over {} PRA in {}/5, {}/10, and {}/25'.format(thres_pra, sum(l5['PRA'] >= thres_pra), sum(l10['PRA'] >= thres_pra), sum(l25['PRA'] >= thres_pra) ) )
    with c2:
        st.subheader('...at home:')
        gamelog_home = gamelog[gamelog['HOME/AWAY']=='HOME']
        l5 = gamelog_home[gamelog_home['NAME']==player_subset].head(5)
        l10 = gamelog_home[gamelog_home['NAME']==player_subset].head(10)
        l25 = gamelog_home[gamelog_home['NAME']==player_subset].head(25)

        st.write('...over {} points in {}/5, {}/10, and {}/25'.format(thres_pts, sum(l5['PTS'] >= thres_pts), sum(l10['PTS'] >= thres_pts), sum(l25['PTS'] >= thres_pts) ) )
        st.write('...over {} rebounds in {}/5, {}/10, and {}/25'.format(thres_reb, sum(l5['REB'] >= thres_reb), sum(l10['REB'] >= thres_reb), sum(l25['REB'] >= thres_reb) ) )
        st.write('...over {} assists in {}/5, {}/10, and {}/25'.format(thres_ast, sum(l5['AST'] >= thres_ast), sum(l10['AST'] >= thres_ast), sum(l25['AST'] >= thres_ast) ) )
        st.write('...over {} threes in {}/5, {}/10, and {}/25'.format(thres_3pm, sum(l5['3PM'] >= thres_3pm), sum(l10['3PM'] >= thres_3pm), sum(l25['3PM'] >= thres_3pm) ) )
        st.write('...over {} PRA in {}/5, {}/10, and {}/25'.format(thres_pra, sum(l5['PRA'] >= thres_pra), sum(l10['PRA'] >= thres_pra), sum(l25['PRA'] >= thres_pra) ) )
    with c3:
        st.subheader('...on the road:')
        gamelog_away = gamelog[gamelog['HOME/AWAY']=='AWAY']
        l5 = gamelog_away[gamelog_away['NAME']==player_subset].head(5)
        l10 = gamelog_away[gamelog_away['NAME']==player_subset].head(10)
        l25 = gamelog_away[gamelog_away['NAME']==player_subset].head(25)

        st.write('...over {} points in {}/5, {}/10, and {}/25'.format(thres_pts, sum(l5['PTS'] >= thres_pts), sum(l10['PTS'] >= thres_pts), sum(l25['PTS'] >= thres_pts) ) )
        st.write('...over {} rebounds in {}/5, {}/10, and {}/25'.format(thres_reb, sum(l5['REB'] >= thres_reb), sum(l10['REB'] >= thres_reb), sum(l25['REB'] >= thres_reb) ) )
        st.write('...over {} assists in {}/5, {}/10, and {}/25'.format(thres_ast, sum(l5['AST'] >= thres_ast), sum(l10['AST'] >= thres_ast), sum(l25['AST'] >= thres_ast) ) )
        st.write('...over {} threes in {}/5, {}/10, and {}/25'.format(thres_3pm, sum(l5['3PM'] >= thres_3pm), sum(l10['3PM'] >= thres_3pm), sum(l25['3PM'] >= thres_3pm) ) )
        st.write('...over {} PRA in {}/5, {}/10, and {}/25'.format(thres_pra, sum(l5['PRA'] >= thres_pra), sum(l10['PRA'] >= thres_pra), sum(l25['PRA'] >= thres_pra) ) )




## Associated detailed data / descriptions
st.header('Full Game Log for Chosen Player')
st.write('If a player is chosen with the filter menu on the left, it will show the game log of that player. Otherwise, it will show the full game log for all possible players and teams.')
st.write('Game log is current as of: {}'.format( gamelog['DATE'].max().strftime('%b %d, %Y') ) )


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