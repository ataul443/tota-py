# -*- coding: utf-8 -*-
import logging
import os
import pickle
import re
from time import time
from multiprocessing import Pool
from user import Verto
from mte import Midterm

import redis
from telegram import InlineKeyboardButton as ikb
from telegram import InlineKeyboardMarkup as ikm
from telegram import ChatAction, Update, ParseMode
from telegram.ext import (CallbackQueryHandler, CommandHandler,
                          ConversationHandler, Filters, MessageHandler,
                          Updater)
from telegram.ext.dispatcher import run_async

from assingment import Resources
from message import Message

##Var, keyboards Declarations--

token = os.environ['TELEGRAM_TOKEN']
PORT = int(os.environ.get('PORT', '5000'))
redis_url = os.getenv('REDIS_URL')
db = redis.from_url(redis_url)

logging.basicConfig(level = logging.DEBUG,
            format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s')

CHOOSING, TYPING_REPLY, TYPING_CHOICE, LOAD = range(4)

reply_keyboared_reg = [[ikb('Reg. Number',callback_data='Reg. Number'), ikb('Password',callback_data='Password')]]
reply_keyboared_options = [[ikb('Messages',callback_data='Messages')
                            ,ikb('Resources',callback_data='Resources')
                            ,ikb('MTE Marks',callback_data='marks')]]

markup_reg = ikm(reply_keyboared_reg)
markup_options = ikm(reply_keyboared_options)

##Database Methods
def delme(bot,update):
    chat_id = update.message.chat_id
    db.delete(chat_id,'{}-msg'.format(chat_id),'{}-courselist'.format(chat_id),'{}-mte'.format(chat_id))
    update.message.reply_text('Your data is erased.\nPlease press "Setup" to register.'
    ,reply_markup = ikm([[ikb('Setup',callback_data='Setup')]]))
    return -1

def database(name,key):
    value = db.hget(name,key)
    value = value.decode('UTF-8')
    return value

##Bot- Methods

@run_async
def start(bot,update):
    chat_id = update.message.chat_id
    if (db.hexists(chat_id,'regNumber')) and (db.hexists(chat_id,'umsPass') and (db.exists('{}-msg'.format(chat_id)))):
        user = update.message.from_user
        user_full_name = '{} {}'.format(user.first_name,user.last_name)
        update.message.reply_text('Welcome back {}'.format(user_full_name)
        ,reply_markup = markup_options)
        return
    else:
        update.message.reply_text(
                        "Hi Dear\n\n"
                        "I hope you are fine. My name is *ToTa*  "
                        "I am your personal bot to handle your daily tedious tasks of UMS "
                        "\n\nI am created by *Shekh Ataul*\nA.K.A -- *DEVIL!*"
                        "\n\nTo Get Started Press: *Setup*",
                        reply_markup = ikm([[ikb('Setup',callback_data='Setup')]]),
                        parse_mode=ParseMode.MARKDOWN)


@run_async
def setup(bot, update):
    query = update.callback_query
    bot.send_chat_action(chat_id=query.message.chat_id, action=ChatAction.TYPING)
    bot.edit_message_text(text="First Time Setup: \n\nYou have to enter your *Registration Number* and *UMS Password* to use me.",
                        chat_id=query.message.chat_id,
                        message_id=query.message.message_id,
                        reply_markup = markup_reg,
                        parse_mode=ParseMode.MARKDOWN)    
    return CHOOSING
@run_async
def user_choice(bot, update, user_data):
    query = update.callback_query
    bot.send_chat_action(chat_id=query.message.chat_id, action=ChatAction.TYPING)
    user_data['choice'] = query.data
    bot.edit_message_text(text="Enter your %s" % query.data,
                     chat_id=query.message.chat_id,
                     message_id=query.message.message_id)
    return TYPING_REPLY

@run_async
def received_information(bot, update, user_data):
    chat_id = update.message.chat_id
    text = update.message.text
    reg_pattern = re.compile(r"^[0-9]*$")
    category = user_data['choice']
    regNumber = None
    umsPass = None
    bot.send_chat_action(chat_id=update.message.chat_id, action=ChatAction.TYPING,timeout=3)
    if (category == 'Reg. Number'):
        if (re.match(reg_pattern, text)and len(text) <= 8):
            user_data[category] = text
            db.hset(chat_id,'regNumber',text)
            del user_data['choice']
            update.message.reply_text(
                "Now click on Password",
                reply_markup = markup_reg)
            return CHOOSING
        else:
            update.message.reply_text(
                "Please enter a valid %s!" % user_data['choice'])
        return TYPING_REPLY
    else:
        user_data[category] = text
        umsPass = text
        db.hset(chat_id,'umsPass',umsPass)
        del user_data['choice']
        update.message.reply_text("Thanks for entering Password!",
        reply_markup=ikm([[ikb('Load Data',callback_data='load')]]))
        return LOAD


@run_async
def loadData(bot,update):
    query = update.callback_query
    chat_id = query.message.chat_id
    regNumber = database(chat_id,'regNumber')
    umsPass = database(chat_id,'umsPass')
    home_test = homeData(bot,update,regNumber,umsPass,chat_id,query)
    if home_test != -1:
        chat_msg_key = '{}-msg'.format(chat_id)
        msgUms = Message(home_test)
        msgList = msgUms.initiater()
        msgtemp = {}
        for i, item in enumerate(msgList):
            if item != '':
                item = ('|').join(item)
                msgtemp['msg{}'.format(i)] = item
        db.hmset(chat_msg_key,msgtemp)
        bot.edit_message_text(text="All set, Now what you want to know about?",
        chat_id=chat_id,message_id=query.message.message_id,
        reply_markup=markup_options)   
        return -1
    else:
        return CHOOSING
        

##Data Readerdef course():
def homeData(bot,update,regNumber,umsPass,chat_id,query=None):
    try:
        homeUms = Verto(regNumber,umsPass)
        homeData, session = homeUms.initiater()
        if homeData != None:
            sess_start = time()
            db.hset(chat_id,'sess_start',sess_start)
            sess_obj = pickle.dumps(session)
            db.hset(chat_id,'sess_obj',sess_obj)
            return homeData
        else:
            db.hdel(chat_id,'regNumber','umsPass')
            raise ValueError("Something Went Wrong")   
    except ValueError as error:
        bot.edit_message_text(text='Incorrect Reg. Number or Password\nPlease try again.',
                                chat_id=chat_id,
                                message_id=query.message.message_id,
                                reply_markup=markup_reg)
        return -1

def msg_reader(bot,update,chat_id):
    chat_id = chat_id
    regNumber = database(chat_id,'regNumber')
    umsPass = database(chat_id,'umsPass')
    home_test = homeData(bot,update,regNumber,umsPass,chat_id)
    if home_test:
        chat_msg_key = '{}-msg'.format(chat_id)
        msgUms = Message(home_test)
        msgList = msgUms.initiater()
        counter = len(msgList)
        for i, item in enumerate(msgList):
            if item != '':             
                annc_sub,annc_by,annc_body = item
            if i == counter-1:
                bot.send_message(text=annc_sub+'\n\n'+annc_by+'\n\n'+annc_body,chat_id=chat_id,reply_markup=markup_options)
            else:
                bot.send_message(text=annc_sub+'\n\n'+annc_by+'\n\n'+annc_body,chat_id=chat_id)
def course_db(bot,update,reg_num,ums_pass,chat_id,query):
    time_stamp = time()
    sess_start = database(chat_id,'sess_start')
    if time_stamp - float(sess_start) <= 180:
        pickled_sess = db.hget(chat_id,'sess_obj')
        sess = pickle.loads(pickled_sess)
    else:
        home_page = homeData(bot,update,reg_num,ums_pass,chat_id,query)
        if home_page:
            pickled_sess = db.hget(chat_id,'sess_obj')
            sess = pickle.loads(pickled_sess)
        else:
            return
    chat_course_list = '{}-courselist'.format(chat_id)
    courseRes = Resources(sess)
    courseBtDict = courseRes.course_codes()
    db.hmset(chat_course_list,courseBtDict)

@run_async
def options(bot,update):
    print("Optins function starting......")
    query = update.callback_query
    chat_id = query.message.chat_id
    choice = query.data
    if choice == "Messages":
        msg_reader(bot,update,chat_id)
        
    elif choice == "Resources":
        regNumber = database(chat_id,'regNumber')
        umsPass = database(chat_id,'umsPass')
        course_db(bot,update,regNumber,umsPass,chat_id,query)
        course_markup = []
        temp = []
        t = []
        course_key = '{}-courselist'.format(chat_id)
        p = db.hkeys(course_key)
        num_courses = len(p)
        for i,item in enumerate(p):
            p[i] = item.decode('UTF-8')
        for i in range(0,num_courses,2):
            key = '{}'.format(p[i])
            if i+1 < num_courses:
                key1 = '{}'.format(p[i+1])
                course_markup.append([ikb(key,callback_data=key),
                                    ikb(key1,callback_data=key1)])
            else:
                course_markup.append([ikb(key,callback_data=key)])
        bot.send_message(text="Choose Subject --",chat_id=chat_id,reply_markup=ikm(course_markup))
    else:
        update.message.reply_text("Sorry Wrong Input!")
        return

@run_async
def course_selected_data(bot, update):
    print('Course selected data Started')
    query = update.callback_query
    chat_id = query.message.chat_id
    course_selected = query.data
    regNumber = database(chat_id,'regNumber') 
    umsPass = database(chat_id,'umsPass')
    time_stamp = time()
    sess_start = database(chat_id,'sess_start')
    if time_stamp - float(sess_start) <= 180:
        pickled_sess = db.hget(chat_id,'sess_obj')
        sess = pickle.loads(pickled_sess)
    else:
        home_page = homeData(bot,update,regNumber,umsPass,chat_id,query)
        if home_page:
            sess = db.hget(chat_id,'sess_obj')
            sess = pickle.loads(sess)
        else:
            return
    course_data = Resources(sess,course_selected)
    course_data_list = course_data.course_content_list()
    for i,item in enumerate(course_data_list):
        txt = item[-1]
        start = txt.find('$lblFileUplaodByTeacher')
        txt = txt[start-5:start]
        if item[2] == u'\xa0':
            item[2] = ''
        res_num_markup = ikm([[ikb('Download',callback_data='hot{}YinZ{}'.format(course_selected,txt))]])
        text_data = 'Course - {}\n{} \n\n {}\n\n {}'.format(course_selected,item[0],item[1].strip(),item[2].strip())
        bot.send_message(text=text_data,chat_id=chat_id,reply_markup=res_num_markup)
        x = '|'.join(item)
        db.hset(chat_id,'{}_{}'.format(course_selected,item[-1]),x)
    
    
@run_async
def res_download(bot, update):
    query = update.callback_query
    chat_id = query.message.chat_id
    temp = query.data
    ##
    n = temp.find('Z')
    value = temp[n+1:]
    n = temp.find('Y')
    course = temp[3:n]
    print(course)
    temp = '{}_ctl00$cphHeading$rgAssignment$ctl00${}$lblFileUplaodByTeacher'.format(course,value)
    ##
    res_data = database(chat_id,temp)
    print(res_data)
    res_data = res_data.split('|')
    res_button = res_data[-1]
    print(res_button)
    regNumber = database(chat_id,'regNumber')
    umsPass = database(chat_id,'umsPass')
    time_stamp = time()
    sess_start = database(chat_id,'sess_start')
    if time_stamp - float(sess_start) <= 180:
        pickled_sess = db.hget(chat_id,'sess_obj')
        sess = pickle.loads(pickled_sess)
    else:
        home_page = homeData(bot,update,regNumber,umsPass,chat_id,query)
        if home_page:
            sess = db.hget(chat_id,'sess_obj')
            sess = pickle.loads(sess)
        else:
            return
    downInst = Resources(sess,course=course)
    @run_async
    def uploader():
        file_name = downInst.initiater(res_button)
        bot.send_document(chat_id=chat_id, document=open('{}'.format(file_name),'rb'))
    uploader()
@run_async
def term_selector(bot,update):
    query = update.callback_query
    chat_id = query.message.chat_id
    regNumber = database(chat_id,'regNumber')
    umsPass = database(chat_id,'umsPass')
    time_stamp = time()
    sess_start = database(chat_id,'sess_start')
    if time_stamp - float(sess_start) <= 180:
        pickled_sess = db.hget(chat_id,'sess_obj')
        sess = pickle.loads(pickled_sess)
    else:
        home_page = homeData(bot,update,regNumber,umsPass,chat_id,query)
        if home_page:
            sess = db.hget(chat_id,'sess_obj')
            sess = pickle.loads(sess)
        else:
            return
    mte = Midterm(sess)
    mte.token_creator(mte.base_page)
    term_list = mte.term_list
    keyboared = []
    for index,item in enumerate(term_list):
        if item != None:
            keyboared.append([ikb(item,callback_data='term_{}_{}'.format(item,index))])
    reply_keyboared_term = ikm(keyboared)
    bot.send_message(text="Choose Term -",chat_id=chat_id,reply_markup=reply_keyboared_term)

@run_async
def mte_marks(bot,update):
    query = update.callback_query
    chat_id = query.message.chat_id
    data = query.data
    temp ,term_code , term_index = data.split('_')
    key_mte = '{}-mte'.format(chat_id)
    if db.exists(key_mte):
        marks_data = db.hkeys(key_mte)
        for item in marks_data:
            if item == term_code:
                k = database(key_mte,term_code)
                course_code, course_name, marks_obt = k.split('_')
                bot.send_message(chat_id=chat_id,text='{}\n\n{}\n\n Marks Obtain : {}'.format(course_code,course_name,marks_obt))
    else:
        regNumber = database(chat_id,'regNumber')
        umsPass = database(chat_id,'umsPass')
        time_stamp = time()
        sess_start = database(chat_id,'sess_start')
        if time_stamp - float(sess_start) <= 180:
            pickled_sess = db.hget(chat_id,'sess_obj')
            sess = pickle.loads(pickled_sess)
        else:
            home_page = homeData(bot,update,regNumber,umsPass,chat_id,query)
            if home_page:
                sess = db.hget(chat_id,'sess_obj')
                sess = pickle.loads(sess)
            else:
                return
        mte = Midterm(sess)

        marks_dict = mte.initiater(term_code,term_index)
        for item in marks_dict:
            course_code, course_name = item.split('::')
            db.hset(key_mte,term_code,'{}_{}_{}'.format(course_code,course_name,marks_dict[item]))
            bot.send_message(chat_id=chat_id,text='{}\n\n{}\n\n Marks Obtain : {}'.format(course_code,course_name,marks_dict[item]))

##Bot,Updater,Dispatcher--
##
updater = Updater(token)
dispatcher = updater.dispatcher

#Handlers--
start_handler = CommandHandler('start',start)
msg_handler = CallbackQueryHandler(options,pattern='^(Messages|Resources)$')
course_selected_handler = CallbackQueryHandler(course_selected_data,pattern="^(?=.*[A-Z])(?=.*[0-9])[A-Z0-9]+$")
res_down_handler = CallbackQueryHandler(res_download,pattern='^(hot)')
marks_handler = CallbackQueryHandler(term_selector,pattern='^marks$')
mte_marks_handler = CallbackQueryHandler(mte_marks,pattern='^term')
delme_handler = CommandHandler('delme',delme)
conv_handler = ConversationHandler(
        entry_points = [CallbackQueryHandler(setup,pattern='^Setup$')],
        states =  {
            CHOOSING:[CallbackQueryHandler(user_choice, pattern='^(Reg. Number|Password)$',
                                    pass_user_data=True)],
            #TYPING_CHOICE:[MessageHandler(Filters.text, user_choice,
                                        #pass_user_data = True)],
            TYPING_REPLY:[MessageHandler(Filters.text,
                                            received_information,
                                            pass_user_data = True)],
            LOAD: [CallbackQueryHandler(loadData,pattern='^load$')],
        
        },
        fallbacks = [])

#WebHook--
dispatcher.add_handler(start_handler)
dispatcher.add_handler(msg_handler)
dispatcher.add_handler(conv_handler)
dispatcher.add_handler(res_down_handler)
dispatcher.add_handler(course_selected_handler)
dispatcher.add_handler(marks_handler)
dispatcher.add_handler(mte_marks_handler)
dispatcher.add_handler(delme_handler)
updater.start_webhook(listen="0.0.0.0",
                      port=PORT,
                      url_path=token)
updater.bot.set_webhook("https://totalpu.herokuapp.com/" + token)