# -*- coding: utf-8 -*-
"""
/***************************************************************************
 YandexTransport
                                 A QGIS plugin
 Layers with transport data from Yandex
                              -------------------
        begin                : 2015-06-27
        git sha              : $Format:%H$
        copyright            : (C) 2015 by yellow_sky
        email                : nikulin.e at gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
import traceback
from PyQt4 import QtCore

import xml.etree.ElementTree as ET
import urllib2
from PyQt4.QtCore import QObject, QThread
from os import path
import qgis
from qgis.core import QgsPoint, QgsMessageLog, QgsVectorLayer, QgsFeature, QgsGeometry

TROLLEY = 'trolleybus'
TRAM = 'tramway'
BUS = 'bus'
MINIBUS = 'minibus'

url = 'http://http.mob.maps.yandex.net/transport/masstransit/1.x/trajectories?l=mtr&lang=en_RU&ll=37.632495%2C55.749792&origin=mobile.transport&spn=0.0822280%2C0.08235675'

class DataSourceUpdater(QThread):

    data_updated = QtCore.pyqtSignal()
    update_error = QtCore.pyqtSignal(Exception, basestring)

    def __init__(self, data_dict, period=1000):
        super(DataSourceUpdater, self).__init__()
        self.killed = False
        self.paused = True
        self.period = period
        self._data_dict = data_dict

    def run(self):
        while not self.killed:
            if not self.paused:
                try:
                    response = urllib2.urlopen(url)  # +str(random.randint(1,1000)))
                    res_xml = response.read()
                    tree = ET.fromstring(res_xml)

                    for e in tree[0][0]:
                        metadata = e[0]
                        transport = metadata[0][1]

                        vech_id = transport[0].text
                        vech_num = transport[1].text
                        vech_type = transport[2].text

                        geo_objs = e[1]
                        coords_txt_1 = geo_objs[0][1][0].text
                        coords_time_1 = geo_objs[0][0][0][0].text

                        coords = coords_txt_1.split(' ')
                        x = coords[0]
                        y = coords[1]

                        #QgsMessageLog.logMessage('x: %s   y: %s' % (x, y), level=QgsMessageLog.INFO)

                        self._data_dict[vech_id] = {
                            'id': vech_id,
                            'type': vech_type,
                            'number': vech_num,
                            'time': coords_time_1,
                            'coord': QgsPoint(float(x), float(y)),
                        }

                    self.data_updated.emit()

                except Exception, e:
                    self.update_error.emit(e, traceback.format_exc())
            self.msleep(self.period)



class YandexTransportDataSource(QObject):
    def __init__(self):
        super(YandexTransportDataSource, self).__init__()
        self._layer_registry = []
        self._data = dict()
        self._period = 5000
        self._updater = DataSourceUpdater(self._data, self._period)
        self._updater.data_updated.connect(self._on_data_update)
        self._updater.update_error.connect(self._on_update_error)
        self._updater.start()

    @property
    def update_period(self):
        return self._period

    @update_period.setter
    def update_period(self, val):
        if not isinstance(val, int):
            raise ValueError('Need int!')
        self._period = val
        self._updater.period = val

    def get_layer(self, type):
        uri = 'point?crs=epsg:4326&field=id:string&field=type:string&field=number:string&field=time:string'
        new_lyr = QgsVectorLayer(uri, 'Yandex Transport', 'memory')

        layer_style_path = path.join(path.dirname(__file__), 'styles/', 'all.qml')
        if path.isfile(layer_style_path):
            new_lyr.loadNamedStyle(layer_style_path)

        self._layer_registry.append(new_lyr)
        self._updater.paused = not len(self._layer_registry)
        return new_lyr

    def resolve_layer(self, lyr):
        if lyr in self._layer_registry:
            self._layer_registry.remove(lyr)
        lyr = None
        self._updater.paused = not len(self._layer_registry)

    def __del__(self):
        self._updater.killed = True

    def _on_data_update(self):
        QgsMessageLog.logMessage('New data recived!', level=QgsMessageLog.INFO)  # 'New data: %s' % str(self._data)
        for lyr in self._layer_registry:
            # clear lyr
            ids = [f.id() for f in lyr.getFeatures()]
            lyr.dataProvider().deleteFeatures(ids)
            # append new features
            features = []
            for data_id, data_obj in self._data.iteritems():
                feat = QgsFeature()
                feat.setAttributes([data_obj['id'], data_obj['type'], data_obj['number'], data_obj['time']])
                feat.setGeometry(QgsGeometry.fromPoint(data_obj['coord']))
                features.append(feat)
            lyr.dataProvider().addFeatures(features)
            #lyr.reload()
            lyr.repaintRequested.emit()
        #qgis.utils.iface.mapCanvas().refresh()

    def _on_update_error(self, exc, error_text):
        QgsMessageLog.logMessage('Data updater raised an exception: %s' % (exc.message), level=QgsMessageLog.CRITICAL)

