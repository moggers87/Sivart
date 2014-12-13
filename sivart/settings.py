##
#    Copyright (C) 2014 Matt Molyneaux
#    Copyright (C) 2014 Jessica Tallon & Matt Molyneaux
#
#    This file is part of Sivart
#
#    Sivart is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    Sivart is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with Sivart.  If not, see <http://www.gnu.org/licenses/>.
##

from subprocess import Popen, PIPE
import os
import stat
import warnings

from django.contrib.messages import constants as message_constants
from django.core import exceptions

import configobj
import validate

##
# Most configuration can be done via settings.ini
#
# The file is searched for in the follow way:
# 1. The environment variable "SIVART_CONFIG", which contains an absolute path
# 2. ~/.config/sivart/settings.ini
# 3. settings.ini in the same folder as this file
#
# See config_spec.ini for defaults, see below for comments
##

# Shorthand for Django's default database backends
db_dict = {
    "postgresql": "django.db.backends.postgresql_psycopg2",
    "mysql": "django.db.backends.mysql",
    "oracle": "django.db.backends.oracle",
    "sqlite": "django.db.backends.sqlite3",
    }

# Shorthand for Django's default database backends
cache_dict = {
    "database": "django.core.cache.backends.db.DatabaseCache",
    "dummy": "django.core.cache.backends.dummy.DummyCache",
    "file": "django.core.cache.backends.filebased.FileBasedCache",
    "localmem": "django.core.cache.backends.locmem.LocMemCache",
    "memcached": "django.core.cache.backends.memcached.PyLibMCCache",
    }

is_testing = bool(int(os.getenv('SIVART_TESTING', '0')))

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

user_config_path = os.path.join(os.path.expanduser("~"), ".config", "sivart", "settings.ini")

if os.path.exists(os.getenv('SIVART_CONFIG', '')):
    CONFIG_PATH = os.getenv('SIVART_CONFIG')
elif os.path.exists(user_config_path):
    CONFIG_PATH = user_config_path
elif os.path.exists(os.path.join(BASE_DIR, "settings.ini")):
    CONFIG_PATH = os.path.join(BASE_DIR, "settings.ini")
elif is_testing:
    CONFIG_PATH = ""
else:
    raise exceptions.ImproperlyConfigured("You must provide a settings.ini file")

# Check that our chosen settings file cannot be interacted with by other users
try:
    mode = os.stat(CONFIG_PATH).st_mode
except OSError:
    warnings.warn("Couldn't find settings.ini", ImportWarning)
else:
    if mode & stat.S_IRWXO != 0:
        warnings.warn("Other users could be able to interact with your settings file. Please check file permissions on %s" % CONFIG_PATH)

config_spec = os.path.join(BASE_DIR, "sivart", "settings_spec.ini")

config = configobj.ConfigObj(CONFIG_PATH, configspec=config_spec)
config.validate(validate.Validator())


# TODO: These could be merged into a custom validator
try:
    SECRET_KEY = config["general"]["secret_key"]
except KeyError:
    if is_testing:
        warnings.warn("You haven't set 'secret_key' in your settings.ini", ImportWarning)
    else:
        raise exceptions.ImproperlyConfigured("You must set 'secret_key' in your settings.ini")

if len(config["general"]["admin_names"]) != len(config["general"]["admin_emails"]):
    raise exceptions.ImproperlyConfigured("You must have the same number of admin_names as admin_emails settings.ini")

# Admins (and managers)
ADMINS = zip(config["general"]["admin_names"], config["general"]["admin_emails"])

# List of hosts allowed
ALLOWED_HOSTS = config["general"]["allowed_hosts"]

# Enable debugging - DO NOT USE IN PRODUCTION
DEBUG = config["general"]["debug"]

# Where `manage.py collectstatic` puts static files
STATIC_ROOT = os.path.join(BASE_DIR, config["general"]["static_root"])

# Email the server uses when sending emails
SERVER_EMAIL = config["general"]["server_email"]

# Site name used in page titles
SITE_NAME = config["general"]["site_name"]

# Link to source code
SOURCE_LINK = config["general"]["source_link"]

# Language code, e.g. en-gb
LANGUAGE_CODE = config["general"]["language_code"]

# Time zone
TIME_ZONE = config["general"]["time_zone"]

# Databases!
DATABASES = {
    'default': {
        'ENGINE': db_dict[config["database"]["engine"]],
        'USER': config["database"]["user"],
        'PASSWORD': config["database"]["password"],
        'HOST': config["database"]["host"],
        'PORT': config["database"]["port"],
    }
}

# "name" is a path for sqlite databases
if config["database"]["engine"] == "sqlite":
    DATABASES["default"]["NAME"] = os.path.join(BASE_DIR, config["database"]["name"])
else:
    DATABASES["default"]["NAME"] = config["database"]["name"]

# Caches!
CACHES = {
    'default': {
        'BACKEND': cache_dict[config["cache"]["backend"]],
        'TIMEOUT': config["cache"]["timeout"],
    }
}

if config["cache"]["backend"] == "file":
    if config["cache"]["location"] == "":
        # sane default for minimum configuration
        CACHES["default"]["LOCATION"] = os.path.join(BASE_DIR, "sivart_cache")
    else:
        CACHES["default"]["LOCATION"] = os.path.join(BASE_DIR, config["cache"]["location"])
else:
    CACHES["default"]["LOCATION"] = config["cache"]["location"]

if not DEBUG:
    # These security settings are annoying while debugging
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True

INSTALLED_APPS = (
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'south',
    'sivart',
)

if DEBUG:
    INSTALLED_APPS += ('debug_toolbar', )

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.static",
    "django.core.context_processors.tz",
    "django.core.context_processors.request",
    "django.contrib.messages.context_processors.messages",
    "sivart.context_processors.reduced_settings_context"
)

# Make sure all custom template tags are thread safe
# https://docs.djangoproject.com/en/1.6/howto/custom-template-tags/#template-tag-thread-safety
TEMPLATE_LOADERS = (
    ('django.template.loaders.cached.Loader', (
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
    )),
)

MESSAGE_TAGS = {message_constants.ERROR: 'danger'}

SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'

ROOT_URLCONF = 'sivart.urls'
WSGI_APPLICATION = 'sivart.wsgi.application'

USE_I18N = True
USE_L10N = True
USE_TZ = True

STATIC_URL = '/static/'

try:
    process = Popen("git rev-parse HEAD".split(), stdout=PIPE, close_fds=True, cwd=BASE_DIR)
    output = process.communicate()[0].strip()
    if not process.returncode:
        os.environ["SIVART_COMMIT_ID"] = output
    else:
        os.environ["SIVART_COMMIT_ID"] = "UNKNOWN"
except OSError, TypeError:
    os.environ["SIVART_COMMIT_ID"] = "UNKNOWN"
