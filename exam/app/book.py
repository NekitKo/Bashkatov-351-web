from flask import Blueprint, render_template, redirect, url_for, flash, request

bp = Blueprint('book', __name__, url_prefix='/book')

# добавить блупринты