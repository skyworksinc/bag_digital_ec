# -*- coding: utf-8 -*-

"""The XBase digital standard cell library.

This library consists entirely of subclasses of LaygoBase or DigitalBase.  The LaygoBase
classes all have the following conventions:

1. row types = ['nch', 'pch'], with orientations = ['MX', 'R0'].
2. only sources are connected to supplies.  The supply wires are cented on top and bottom boundaries.
"""
