from flask import render_template

import app.helpers.point_form
from app.helpers.transnet_download_user_form import TransnetDownloadUserForm
from app.models.transnet_country import TransnetCountry
from app.models.transnet_stats import TransnetStats


class ApplicationController:
    def index(self):
        point_form = app.helpers.point_form.PointForm()
        voltages = TransnetCountry.get_voltages()
        world = TransnetCountry.get_countries()
        last_updated = TransnetStats.get_last_updated()
        download_user_form = TransnetDownloadUserForm()
        return render_template('map.html', point_form=point_form, voltages=voltages, world=world,
                               last_updated=last_updated, download_user_form=download_user_form)

    def update(self):
        return None

    def page500(self):
        return render_template('500.html')

    def page403(self):
        return render_template('403.html')
