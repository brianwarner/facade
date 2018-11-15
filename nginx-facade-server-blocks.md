Here is how I configured the nginx server to serve up facade .... 


## Setting Up Server Blocks (Pretty much necessary if you are running more than one website on the server.)

When using the Nginx web server, you can use server blocks (similar to virtual hosts in Apache) to encapsulate configuration details and host more than one domain from a single server. We will set up a domain called facade, but you should replace this with your own domain name.

Create the directory for facade, using the -p flag to create any necessary parent directories:

> sudo mkdir -p /var/www/facade/html

Assign ownership of the directory:

>sudo chown -R $USER:$USER /var/www/facade/html

The permissions of your web roots should be correct if you haven't modified your umask value, but you can make sure by typing:

>sudo chmod -R 755 /var/www/facade

Create a sample index.html page using nano or your favorite editor:

>nano /var/www/facade/html/index.html

Inside, add the following sample HTML:

/var/www/facade/html/index.html

```html
<html>
    <head>
        <title>Welcome to facade!</title>
    </head>
    <body>
        <h1>Success!  The facade server block is working!</h1>
    </body>
</html>
```

Save and close the file when you are finished.

Make a new server block at /etc/nginx/sites-available/facade:

> sudo nano /etc/nginx/sites-available/facade

Paste in the following configuration block, updated for our new directory and domain name:


/etc/nginx/sites-available/facade

```bash
server {
        listen 80;
        listen [::]:80;

        root /var/www/facade/html;
        index index.html index.htm index.nginx-debian.html;

        server_name facade www.facade;

        location / {
                try_files $uri $uri/ =404;
        }
}
```


Save and close the file when you are finished.

Enable the file by creating a link from it to the sites-enabled directory:

> sudo ln -s /etc/nginx/sites-available/facade

/etc/nginx/sites-enabled/

Two server blocks are now enabled and configured to respond to requests based on their listen and server_name directives:

facade: Will respond to requests for facade and www.facade.
default: Will respond to any requests on port 80 that do not match the other two blocks.
To avoid a possible hash bucket memory problem that can arise from adding additional server names, it is necessary to adjust a single value in the /etc/nginx/nginx.conf file. Open the file:

> sudo nano /etc/nginx/nginx.conf

Find the server_names_hash_bucket_size directive and remove the # symbol to uncomment the line:

/etc/nginx/nginx.conf

```bash
http {
    ...
    server_names_hash_bucket_size 64;
    ...
}
```

Test for syntax errors:

> sudo nginx -t

Restart Nginx to enable your changes:

> sudo systemctl restart nginx

Nginx should now be serving your domain name. You can test this by navigating to http://facade, where you should see something like this:

Nginx first server block
