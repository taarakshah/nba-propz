import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

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

    players5 = players[players['mpg'] >= 5.0].sort_values(by='team').reset_index(drop=True)
    ## split the .php ending for each player to get game log links..need it like trae-young.php, luka-doncic.php, etc
    phplist = []
    for i in range(len(players5.href)):
        php = players5['href'].str.split('/')[i][3]
        phplist.append(php)
    ## add it to df
    players5['php'] = phplist
    players = players5.drop(['href','mpg'], axis=1)

    ## Get the URL and HTML content of the game log page
    urlbuild = 'https://www.fantasypros.com/nba/games/' ## need to + the "php" column for each player from previous dataframe, done in loop
    gamelog = pd.DataFrame()
    for i in tqdm(range(len(players.php))):
        ## build URL to pull gamelog from
        url = urlbuild + players['php'][i]
        r = requests.get(url)
        soup = BeautifulSoup(r.content, 'html.parser')
        parsed = soup.find_all('tr')
        ## lists per player
        dates, opps, mins, fgms, fgas, tpms, tpas, ftms, ftas, rebs, asts, tos, stls, blks, pfs, pts, pras = [],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]

        for game in parsed:
            try:
                date = game.find_all('td')[0].get_text()
                opp = game.find_all('td')[1].get_text()
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
                opps.append(opp)
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
            minilog = pd.DataFrame(list(zip(dates, opps, mins, fgms, fgas, tpms, tpas, ftms, ftas, rebs, asts, tos, stls, blks, pfs, pts, pras)), columns=['DATE','OPP','MIN','FGM','FGA','3PM','3PA','FTM','FTA','REB','AST','TO','STL','BLK','PF','PTS','PRA'])

        player_name = players['name'][i]
        player_team = players['team'][i]
        minilog['NAME'] = player_name
        minilog['TEAM'] = player_team
        
        ## combine all player gamelogs
        gamelog = pd.concat([gamelog, minilog], ignore_index=False)

    return gamelog

gamelog = get_new_data()
gamelog.to_csv('gamelog.csv', index=False)