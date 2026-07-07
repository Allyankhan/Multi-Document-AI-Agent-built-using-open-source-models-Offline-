# --- Stage 1: Build the React App ---
FROM node:20-slim AS builder

WORKDIR /app

# Copy package files and install dependencies
COPY package*.json ./
RUN npm install

# Copy application source and build production assets
COPY . .
RUN npm run build

# --- Stage 2: Serve with Nginx ---
FROM nginx:alpine

# Copy the build output from Stage 1 to Nginx's public folder
COPY --from=builder /app/dist /usr/share/nginx/html

# Expose port 80 for the web interface
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]