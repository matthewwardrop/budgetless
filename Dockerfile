FROM codekoala/arch:latest
ENV BUDGETLESS_DATA=/data/budgetless.db
RUN pacman --noconfirm -Syu
RUN pacman --noconfirm -S python-flask python-pip python-pandas python-numpy python-sqlalchemy python-matplotlib gcc cython python-sympy cronie
RUN echo "budgetless ${BUDGETLESS_DATA} sync" > /etc/cron.hourly/budgetless_update
RUN chmod +x /etc/cron.hourly/budgetless_update
MAINTAINER Matthew Wardrop <mister.wardrop@gmail.com>
EXPOSE 5000
RUN pip install gunicorn mintapi plotly parampy
RUN pip install git+https://github.com/matthewwardrop/budgetless.git
RUN mkdir -p $(dirname $BUDGETLESS_DATA)
CMD crond && budgetless ${BUDGETLESS_DATA} deploy
