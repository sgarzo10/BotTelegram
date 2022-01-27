from pyrogram import Client
from time import sleep
from re import escape
from os import remove
from telegram import ReplyKeyboardMarkup
from telegram.ext import Updater, Filters, CommandHandler, CallbackQueryHandler, MessageHandler
from logging import basicConfig, INFO, exception
from json import loads
from hmac import new
from hashlib import sha256
from tabulate import tabulate
from csv import writer
from matplotlib.pyplot import pie, legend, suptitle, axis, figure, close, cla
from matplotlib.backends.backend_pdf import PdfPages
from numpy import array
from json import loads
from meross_iot.api import MerossHttpClient
from logging import exception
from time import sleep
from tabulate import tabulate
from os import listdir, remove, walk, path, makedirs, popen
from shutil import rmtree
from html import unescape
from pytube import YouTube
from pydub import AudioSegment
from zipfile import ZipFile
from subprocess import PIPE, Popen
from os import system
from urllib.request import urlopen, Request
from logging import info, exception
from json import load, dumps
from selenium.webdriver import ChromeOptions, Chrome
from telegram import InlineKeyboardMarkup, InlineKeyboardButton

print("ok")