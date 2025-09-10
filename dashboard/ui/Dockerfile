# Use a lighweight image to build the app
FROM node:24.1-alpine AS builder

WORKDIR /app

# Copy only the files necessary to install dependencies
COPY package.json package-lock.json .

# Install dependencies using npm
RUN npm install;

# Copy the rest of the project files
COPY . .

# Build the app
RUN npm run build

# --------------------

# Use a lighweight image to serve the app
FROM node:24.1-alpine AS runner

WORKDIR /app

# Copy only the files necessary to run the app
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json

# Expose port 3000
EXPOSE 3000

# Start the app
CMD ["npm", "start"]
