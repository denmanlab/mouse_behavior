import glob,os,filecmp,time,schedule,datetime, sys, getopt, requests
from shutil import copytree
# msvcrt is a windows specific native module
import msvcrt
import time
from dlab import dlabbehavior as db
import pandas as pd
from numpy import unique

from slack import WebClient
sc = WebClient(token=os.environ['SLACK_BEHAVIOR_BOT_TOKEN'])



# asks whether a key has been acquired
def kbfunc():
    #this is boolean for whether the keyboard has bene hit
    x = msvcrt.kbhit()
    if x:
        #getch acquires the character encoded in binary ASCII
        ret = msvcrt.getch()
    else:
        ret = False
    return ret


def job():
    folders = [r'C:\Users\denma\Desktop\cheetah_or_elephant',
            r'C:\Users\denma\Desktop\bonsai_levertask',
            r'C:\Users\denma\Desktop\estim_discrimination']
    print('syncing C: to backups at '+datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
    for task in folders:
        task_animals = glob.glob(os.path.join(task,'data')+r'\*')
        for folder in task_animals:
            if 'test' not in folder:
                make_plots=False #used later to determine if we make plots for this animal today
                #if an animal doesn't exist within a task data folder on E: or //DENMANLAB/s1, then make it
                try:
                    if not os.path.isdir(folder.replace('C:\\Users\denma\Desktop','E:')): os.mkdir(folder.replace('C:\\Users\denma\Desktop','E:'))
                    if not os.path.isdir(folder.replace('C:\\Users\denma\Desktop','D:')): os.mkdir(folder.replace('C:\\Users\denma\Desktop','D:'))
                except:pass
                try:
                    if not os.path.isdir(folder.replace('C:\\Users\denma\Desktop','//DENMANLAB/s1/behavior/').replace('\\','/')):os.mkdir(folder.replace('C:\\Users\denma\Desktop','//DENMANLAB/s1/behavior/').replace('\\','/'))
                except:pass 

                #this generates a comparison of the sessions within an animal's folder
                C_D = filecmp.dircmp(folder,folder.replace('C:\\Users\denma\Desktop','D:'))
                C_E = filecmp.dircmp(folder,folder.replace('C:\\Users\denma\Desktop','E:'))
                C_S1 = filecmp.dircmp(folder,folder.replace('C:\\Users\denma\Desktop','//DENMANLAB/s1/behavior/').replace('\\','/'))                        

                #if there are any sessions that are only on the C: drive, then it copies to E: and tries the same to //DENMANLAB/s1 
                if len(C_D.left_only)>0:
                    dates=[]
                    for session in C_D.left_only:
                        if len(C_E.left_only)>0:
                            if session in C_E.left_only:
                                print('syncing C: '+session+' to E: at '+datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
                                #makenwb
                                if 'figs' not in session:
                                    try:
                                        if task==folders[1]: db.make_lever_NWB(os.path.join(folder,session)) 
                                        if task==folders[0]: db.make_discrimination_NWB(os.path.join(folder,session),experiment_description='Denman Lab plaid task | phase:0') 
                                        if task==folders[2]: db.make_discrimination_NWB(os.path.join(folder,session),experiment_description='Denman Lab estim discrim | phase:0') 
                                        make_plots=True
                                        dates.extend([ '_'.join(session.split('-')[0].split('_')[1:4])])
                                    except:make_plots=False
                                    # print('no NWB for '+session)
                                    # make_plots=False
                                #copy it all, including the nwb we just made
                                copytree(os.path.join(folder,session),os.path.join(folder.replace('C:\\Users\denma\Desktop','E:'),session))
                if len(C_S1.left_only)>0:
                    for session in C_S1.left_only:
                        try:
                            print('syncing C '+session+' to DENMANLAB/s1 at '+datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
                            copytree(os.path.join(folder,session),folder.replace('C:\\Users\denma\Desktop','//DENMANLAB/s1/behavior').replace('\\','/')+r'/'+session)
                        except:pass
            
                #make today's figures
                if make_plots:
                    # try:
                    animal = os.path.basename(folder)
                    datestring=datetime.datetime.now().strftime("%Y_%m_%d").replace("_0","_")
                    today = datestring.split('_')[2]
                    tomonth =  datestring.split('_')[1]
                    toyear = datestring.split('_')[0]
                    days =db.get_history_sessions(today,tomonth,toyear)

                    up_to_slack=False
                    if task == folders[0]:#cheetah_or_elephant
                        for datestring in unique(dates):
                            print(datestring)
                            fig = db.generate_session_plaid(animal,datestring,session='combine',return_='fig')
                            if not os.path.exists(os.path.join(folder,'figs')):os.makedirs(os.path.join(folder,'figs'))
                            fig.savefig(os.path.join(folder,'figs',datestring+'_summary.png'))
                            fig.savefig(os.path.join(folder,'figs',datestring+'_summary.eps'),format='eps')
                            pass # fr nw
                            up_to_slack=True
                    if task == folders[2]:#estim_discrimination
                        for datestring in unique(dates):
                            print(datestring)
                            fig = db.generate_session_estim(animal,datestring,session='combine',return_='fig')
                            if not os.path.exists(os.path.join(folder,'figs')):os.makedirs(os.path.join(folder,'figs'))
                            fig.savefig(os.path.join(folder,'figs',datestring+'_summary.png'))
                            fig.savefig(os.path.join(folder,'figs',datestring+'_summary.eps'),format='eps')
                            pass # fr nw
                            up_to_slack=True
                    if task == folders[1]:#lever
                        #generate figures
                        for datestring in unique(dates):
                            try:
                                fig,ax = db.generate_session_lever(animal,datestring,session='combine',return_='fig')
                                date_folder = glob.glob(os.path.join(folder,animal+'_'+datestring+'*'))[-1] 
                                if not os.path.exists(os.path.join(folder,'figs')):os.makedirs(os.path.join(folder,'figs'))
                                fig.savefig(os.path.join(folder,'figs',datestring+'_summary.png'))
                                fig.savefig(os.path.join(folder,'figs',datestring+'_summary.eps'),format='eps')
                                up_to_slack=True
                            except: 
                                print('failed to generaate session figure for '+folder+'  '+datestring+'check the NWBs for this date.')
                                up_to_slack=False

                        #go over previous sessions and make across-session figures 
                        #first, get the strings for the previous ten days. do gymnastics to formats date for bonsai task outputs. 

                        # dfs = [db.generate_session(folder,this_day,session='combine',return_='df') for this_day in days]
                        # df = pd.concat(dfs,ignore_index=True)
                        # fig = db.across_session_plots_lever(df)
                        # if not os.path.exists(os.path.join(folder,'figs')):os.makedirs(os.path.join(folder,'figs'))
                        # fig.savefig(os.path.join(folder,'figs','recent_sessions.png'))
                        # fig.savefig(os.path.join(folder,'figs','recent_sessions.eps'),format='eps')
                    # except: print('failed to make figures for '+folder)
                    #send figures to slack     
                    # message = 'behavior updates for '+animal+' on '+datestring
                    # sc.chat_postMessage( channel="#behavior_plot_bot", text=message)
                    if up_to_slack:
                        response = sc.files_upload(channels="#behavior_plot_bot",file=os.path.join(folder,'figs',datestring+'_summary.png'),title='summary '+animal+' on '+datestring)
                    # response = sc.files_upload(channels="#behavior_plot_bot",
                    #     file=os.path.join(folder,'figs','recent_sessions.png'),
                    #     title='summary '+folder+' on '+datestring)

    print('done syncing C: to backups at '+datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S"))    
       

    return
#run at startup
print('backing up C to DENMANLAB')
job()

#schedule to recur every day at a certain time.
schedule.every().day.at("01:00").do(job)
schedule.every().day.at("17:40").do(job)

while True:
    schedule.run_pending()
    time.sleep(60) # wait one minute
    #if we got a keyboard hit
    x = kbfunc()
    if x != False and x.decode() == 'u':
        #we got the key!
        #because x is a binary, we need to decode to string
        #use the decode() which is part of the binary object
        #by default, decodes via utf8
        #concatenation auto adds a space in between
        job()


#---------------------EXTRA STUFF FROM DEV------------------------------------------------------

def copytree2(source,dest):
    os.mkdir(dest)
    dest_dir = os.path.join(dest,os.path.basename(source))
    copytree(source,dest_dir)


# folders = [r'C:\Users\denma\Desktop\cheetah_or_elephant',
#           r'C:\Users\denma\Desktop\bonsai_levertask']


# for folder in folders:
#     C_D = filecmp.dircmp(os.path.join(folder,'data'),os.path.join('D:\\',os.path.basename(folder),'data'))
#     # C_S1 = filecmp.dircmp(os.path.join(folder,'data'),os.path.join('DENMANLAB','s1','behavior',os.path.basename(folder),'data'))
#     if len(C_D.left_only)>0:
#         for mouse in C_D.left_only:
#             copytree2(os.path.join(folder,'data',mouse),os.path.join('D:\\',os.path.basename(folder),'data',mouse))


# for sess in C_D.left_only:
#     copytree2(folder+r'/'+sess,os.path.join('D:\\','cheetah_or_elephant','data','c63',sess))