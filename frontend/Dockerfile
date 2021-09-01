# Node version that we used.
FROM node:12.18.3-alpine

# Create a work directory and copy over our dependency manifest files.
RUN mkdir /app
WORKDIR /app

# Install app dependencies
COPY package.json ./
COPY package-lock.json ./
RUN npm install

# Add app
COPY . ./

# Start app
CMD ["npm", "start"]
