UvA-Grassroots project Course Attendance Registration: Digitalized (CARD).
=======

**CARD features have been implemented in the existing UvA/FNWI systems. This project is deprecated and no longer in use**

Keywords: Attendance registration, RFID student id card, CARD, University of
Amsterdam.

An attendance registration website will be developed for UvA course Oriëntatie.
The site will be Django based and hosted on tlrh314's home webserver for
development purposes and on the ICTO/FNWI IVO server for production. This
repository open-sources said website.

Course: Oriëntatie Natuur- en Sterrenkunde (OWIN / 5092ORNS3Y)
BSc Natuur- en Sterrenkunde (N&S) (2nd and 3rd year), Faculty of Science,
University of Amsterdam.

For the registration the CARD website will be opened on a laptop with an RFID
reader. Students should `check in' to lectures using their student id card.
For the lecturer it will no longer be necessary to digitalize the sheet of paper
that is currently sent round to register student attendance. Students will be
enabled to monitor their progress for the course at home.

The project is subsidized by the UvA as part of the UvA Grassroots program.

**Software versions**

* Python 2.7.5+
* virtualenv 1.11.2
* Django 1.6.2
* MySQL Ver 14.14 Distrib 5.5.32, for debian-linux-gnu (x86_64)
* Apache/2.4.6
* mod_wsgi-3.4
