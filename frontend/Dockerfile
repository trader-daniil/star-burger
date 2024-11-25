FROM node:18.13.0
WORKDIR /frontend
COPY . .
RUN npm install
RUN ./node_modules/.bin/parcel build bundles-src/index.js --dist-dir bundles --public-url="./"