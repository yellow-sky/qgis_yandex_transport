# -*- coding: utf-8 -*-
"""
/***************************************************************************
 YandexTransport
                                 A QGIS plugin
 Layers with transport data from Yandex
                             -------------------
        begin                : 2015-06-27
        copyright            : (C) 2015 by yellow_sky
        email                : nikulin.e at gmail.com
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load YandexTransport class from file YandexTransport.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .yandex_transport import YandexTransport
    return YandexTransport(iface)
