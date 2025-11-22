# Use the official Nginx image from Docker Hub
FROM nginx:alpine

# Remove the default Nginx welcome page
RUN rm -f /usr/share/nginx/html/index.html

# Copy the static assets to the Nginx web root directory
COPY . /usr/share/nginx/html

# Expose port 80 to the outside world
EXPOSE 80

# Command to run Nginx in the foreground
CMD ["nginx", "-g", "daemon off;"]