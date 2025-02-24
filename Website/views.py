import random
from calendar import weekday

import requests
import datetime
from geopy import Nominatim
from flask import Blueprint, render_template, request, redirect, url_for, current_app
from flask_login import login_required, current_user
from .models import Scoreboard, Quiz, User
from . import db #importing db from __init__.py

views = Blueprint('views', __name__)
utilityDays = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]
utilityMonth = ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno", "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]

@views.route('/', methods=['GET', 'POST'])
@login_required #decorator, prevents user from access this route unless the user is logged in
def home():
    cityName = request.args.get("cityName")
    if cityName is not None:
        try:
            geolocator = Nominatim(user_agent="eleonora.davi@gmail.com")
            location = geolocator.geocode(cityName, addressdetails=True)

            #Left for debug
            #print(location.latitude, location.longitude)
            #print(location.raw)
            apiKey = current_app.config['API_KEY_WEATHER']
            url = "https://api.pirateweather.net/forecast/" + apiKey + "/" + str(location.latitude) + "," + str(location.longitude)

            querystring = {"exclude": "", "extend": "", "lang": "", "units": "ca", "version": "", "tmextra": ""}

            response = requests.get(url, params=querystring)
            print(response.json())

            # Convert json into dictionary
            response_dict = response.json()
            infoList = []
            infoList.append(cityName)
            dateTime = datetime.datetime.today()
            todayDate = str(dateTime.day) + " " + utilityMonth[abs(dateTime.month)] + " " + str(dateTime.year)
            print(todayDate)
            infoList.append(todayDate)
            weekday = datetime.datetime.today().weekday()
            dayofWeek = utilityDays[weekday]
            infoList.append(dayofWeek)
            dailyForecast = response_dict["daily"]
            dailyCastdata = dailyForecast["data"]
            i = 0 #counter for records
            recordlist = []
            for dataRecord in dailyCastdata:
                record = {}
                #To prevent index out of range exception because I only have six days
                if weekday > 4:
                    dayvalue = abs(weekday - (weekday + i))
                    if dayvalue == 0:
                        record["day"] = utilityDays[weekday]
                    else:
                        record["day"] = utilityDays[dayvalue - 1]
                else:
                    record["day"] = utilityDays[weekday]
                record["forecast"] = dataRecord['icon'] #Per evitare la localizzione in inglese, prendo direttamente la designazione come icona
                record["dayTemp"] = dataRecord['temperatureMax'] #La temperatura massima è la diurna
                record["nightTemp"] = dataRecord['temperatureMin'] #La temperatura minima è la notturna
                record["humidity"] = dataRecord['humidity'] * 100 #discrimination variable, for testing purposes

                recordlist.append(record)
                i += 1
                if i == 3:
                    break

            print("DAILY _______________________________________--------->")
            print(response_dict["daily"])
            return render_template("home.html", username=current_user.username, user=current_user, infoList=infoList, recordList=recordlist)
        except:
            return render_template("home.html", username=current_user.username, user=current_user, infoList=None, recordList=None)
    else:
        return render_template("home.html", username = current_user.username, user=current_user, infoList=None, recordList=None)

@views.route('/game', methods=['GET', 'POST'])
@login_required #decorator, prevents user from access this route unless the user is logged in
def game():

    allRecords = Quiz.query.all() #keep a backup of original question - answer structure so another query is unnecessary
    casualRecords = allRecords
    random.shuffle(casualRecords) #Every time the questions are posed in a random shuffle
    userId = current_user.id

    #Each time prepare an appropriate dictionary with current correct answers (after shuffling) ready for quiz evaluations
    correctAnswers = {}
    pointPerQuestion = {}
    for record in allRecords:
        correctAnswers[record.id] = record.correctAns
        pointPerQuestion[record.id] = record.pointValue
    print(correctAnswers)

    #Non implementerò score dinamico mentre si svolge il quiz in tempo reale.
    #Questo meccanismo, aiutato da un check in front-end della risposta corretta, permette di indovinare la risposta giusta e non è indice di conoscenza
    userScore = db.session.query(Scoreboard.userScore).filter_by(userId = userId).first()
    if userScore is None:
        currentScore = 0
    else:
        currentScore = int(userScore.userScore)
    print(currentScore)

    if request.method == 'POST':
        questionIds = request.form.getlist("questionId")
        previousScore = currentScore
        temporaryScore = 0  # the current score to be updated at each quiz evaluation
        correctGiven = 0

        for questionId in questionIds:
            #this variables need to be changed at each loop
            currentQuestion = questionId
            correctAns = correctAnswers[int(currentQuestion)]
            formResponse = request.form.get(currentQuestion)

            print("LOOP START --------->")
            print("Current Question is " + str(currentQuestion))
            print("The correct answer is " + str(correctAns))
            print("FORM RESPONSE")
            print(formResponse)
            print("---------------->")

            if formResponse is not None: #if the question has actually been answered
                if str(formResponse) == str(correctAns):
                    print("For question " + str(currentQuestion) + "option selected was " + formResponse + "and CORRECTEDNESS EVALUATION RETURNED TRUE")
                    temporaryScore = temporaryScore + pointPerQuestion[int(currentQuestion)]
                    correctGiven = correctGiven + 1
            else:
                pass

        userScore = Scoreboard.query.filter_by(userId=userId).with_for_update().first()
        finalScore = userScore.userScore + temporaryScore
        userScore.userScore += temporaryScore
        db.session.commit()

        return redirect(url_for("views.recap", previousScore=previousScore, correctGiven=correctGiven, newScore=finalScore, sessionScore = temporaryScore))

    return render_template("game.html", username = current_user.username, questions=casualRecords, firstActive=casualRecords[0].id, currentScore = currentScore)

@views.route('/scoreboard', methods=['GET', 'POST'])
@login_required #decorator, prevents user from access this route unless the user is logged in
def scoreboard():
    allScoreRecords = Scoreboard.query.all()
    tableScore = []

    for record in allScoreRecords:
        userId = record.userId
        score = record.userScore
        keyPair = {}

        user = db.session.query(User.username).filter_by(id=userId).first()
        if user is not None:
            keyPair["username"] = user.username
            keyPair["score"] = score

            tableScore.append(keyPair)
        else:
            pass
    return render_template("scoreboard.html", username = current_user.username, tableScore=tableScore)

@views.route('/recap', methods=['GET', 'POST'])
@login_required #decorator, prevents user from access this route unless the user is logged in
def recap():
    return render_template("recap.html")

#Random Utility to insert question in Database.
#Left for ease of understanding, obsolete
def addQuestionstoDb():
    questions = {0: "Cosa differenzia un'applicazione NLP (Natural Language Processing), da un software comune?",
                 1: "A cosa si sono ispirati per crare la struttura delle Reti Neurali?",
                 2: "Cosa si intende per Deep Learning?",
                 3: "A cosa mi riferisco quando parlo di Tokenization dei dati?",
                 4: "Qual'è la differenza tra addestramento supervisionato e non supervisionato?",
                 5: "Qual'è stato il primo applicativo di Natural Language Processing mai realizato?",
                 6: "Cosa si intende per Universal Approximation Theorem?",
                 7: "Qual'è il fenomeno che porta l'AI a commettere errori discriminatori sulla base di dati mal distribuiti?",
                 8: "Qual'è uno degli step fondamentali da compiere prima di andare ad addestrare un modello di AI?"
                 }

    answers = {
        0: ["Richiede l'uso della conoscenza del linguaggio umano", "Conta i caratteri in un testo",
            "Genera caratteri casuali", "Riconosce se un carattere è presente in una stringa"],
        1: ["La struttura del cervello biologico, in particolare la connessione tra neuroni", "Un diagramma ad albero",
            "Un diagramma di flusso", "Una mappa concettuale"],
        2: ["Una rete neurale profonda, organizzata a strati, dove ogni strato calcola i valori per quello successivo",
            "Una catena di modelli AI consecutivi", "Un gruppo molto esteso e variegato di dati",
            "Un modello di AI generativa"],
        3: ["Dividere le sequenze di caratteri di un testo in unità minime formattate per l'analisi",
            "Contare quante lettere uguali ci sono nella stessa parola",
            "Un dataset composto solo da gruppi di tre lettere", "Analisi di token presi da internet"],
        4: [
            "Nell'addestramento supervisionato, il set di dati di training contiene informazioni sul significato di tali dati, in quello non supervisionato, i dati sono privi di etichetta",
            "Nell'addestramento supervisionato lo scienziato si occupa di fare i calcoli per aiutare il modello, in quello non supervisionato no",
            "Supervisionato significa che il modello è preaddestrato, quello non supervisionato significa che il modello è 'vuoto'",
            "Supervisionato, a differenza di non supervisionato, implica una migliore performance nei test di validazione"],
        5: [
            "Eliza, creato dal 1964 al 1966 presso il MIT (Massachussets Institute of Technology), primo modello basato su Regular Expressions",
            "Deep Blue, l'agente che vinse contro il campione del mondo di scacchi nel 1996",
            "ChatGPT quando è uscito a Novembre 2022",
            "AlphaGo, modello che battè Fan Hui in una partita di Go nel 2015"],
        6: [
            "Reti Neurali con un solo hidden layer e un numero appropriato di hidden neurons possono approssimare qualsiasi funzione matematica esistente",
            "Tutti i modelli di AI possono essere approssimati da un singolo modello generico",
            "I dati di training di un modello devono essere approssimati secondo regole generali",
            "Approssimare una rete neurale la rende adatta a svolgere qualsiasi tipo di calcolo, che sia esso generativo o predittivo"],
        7: [
            "Il fenomeno di Bias dell'Algoritmo, dove per colpa di un errore nel design o nella qualità dei dati, il modello produce un risultato che è guidato da un 'pregiudizio'",
            "Quando si generano dati con un cattivo prompt",
            "Una mancata attenzione al dato da parte del data scientist",
            "Errore nel calcolo delle metriche statistiche nell'analisi preliminare del dato"],
        8: [
            "Pulire e normalizzare i dati, calcolando le metriche statistiche quali media, mediana e i percentili, e fare encoding dei valori non quantitativi per dare loro significato",
            "Chiedere a ChatGPT se il modello che sto usando è appropriato",
            "Fare una validazione preliminare del modello",
            "Calcolare score ed accuracy del mio modello per verificare che sia pronto al training"]
    }

    if db.session.query(Quiz.id).filter_by(id=0).first() is None:
        for i in range(0, 9):
            print("Loading QUESTIONS AND ANSWERS")
            question = questions[i]
            print(question)
            responses = answers[i]
            print(responses)
            print("Taking in the correct one")
            correct = responses[0]
            print(correct)

            print("Shuffling Answers")
            random.shuffle(responses)
            print(responses)
            print("Loading database values")
            optionOne = responses[0]
            print(optionOne)
            optionTwo = responses[1]
            print(optionTwo)
            optionThree = responses[2]
            print(optionThree)
            optionFour = responses[3]
            print(optionFour)
            print("Saving the correct answer")
            for j in range(0, 4):
                if correct.casefold() == responses[j].casefold():
                    print(responses[j])
                    correctAns = j + 1
                    print(correctAns)
                else:
                    pass
            pointValue = 10

            new_quiz = Quiz(question=question, optionOne=optionOne, optionTwo=optionTwo, optionThree=optionThree,
                        optionFour=optionFour,
                        correctAns=correctAns, pointValue=pointValue)
            db.session.add(new_quiz)
            db.session.commit()
            print("Added question " + str(i) + " to Database")
