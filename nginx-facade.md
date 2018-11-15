## Step 1: Install the php-fpm and php-mysql things
 - sudo apt-get install php-fpm php-mysql

## Step 2: Configure the PHP Processor
We now have our PHP components installed, but we need to make a slight configuration change to make our setup more secure.

Open the main php-fpm configuration file with root privileges:

> sudo vi /etc/php/7.2/fpm/php.ini

What we are looking for in this file is the parameter that sets cgi.fix_pathinfo. This will be commented out with a semi-colon (;) and set to "1" by default.

This is an extremely insecure setting because it tells PHP to attempt to execute the closest file it can find if the requested PHP file cannot be found. This basically would allow users to craft PHP requests in a way that would allow them to execute scripts that they shouldn't be allowed to execute.

We will change both of these conditions by uncommenting the line and setting it to "0" like this:

*/etc/php/7.2/fpm/php.ini*
>cgi.fix_pathinfo=0

Save and close the file when you are finished.

Now, we just need to restart our PHP processor by typing:

> sudo systemctl restart php7.0-fpm

This will implement the change that we made.

## Step 3: Configure Nginx to Use the PHP Processor
Now, we have all of the required components installed. The only configuration change we still need is to tell Nginx to use our PHP processor for dynamic content.

We do this on the server block level (server blocks are similar to Apache's virtual hosts). Open the default Nginx server block configuration file by typing:

> sudo vi /etc/nginx/sites-available/default

Currently, with the comments removed, the Nginx default server block file looks like this:

>/etc/nginx/sites-available/default
server {
>    listen 80 default_server;
>    listen [::]:80 default_server;

>    root /var/www/html;
>    index index.html index.htm index.nginx-debian.html;

>    server_name \_;

>    location / {
>        try_files $uri $uri/ =404;
>    }
>}

We need to make some changes to this file for our site.

First, we need to add index.php as the first value of our index directive so that files named index.php are served, if available, when a directory is requested.

We can modify the server_name directive to point to our server's domain name or public IP address.

For the actual PHP processing, we just need to uncomment a segment of the file that handles PHP requests by removing the pound symbols (#) from in front of each line. This will be the location ~\.php$ location block, the included fastcgi-php.conf snippet, and the socket associated with php-fpm.

We will also uncomment the location block dealing with .htaccess files using the same method. Nginx doesn't process these files. If any of these files happen to find their way into the document root, they should not be served to visitors.

The file should look like what's below:

/etc/nginx/sites-available/default

>server {
>    listen 80 default_server;
>    listen [::]:80 default_server;

>    root /var/www/html;
>    index index.php index.html index.htm index.nginx-debian.html;

>    server_name server_domain_or_IP;

>    location / {
>        try_files $uri $uri/ =404;
>    }

>    location ~ \.php$ {
>        include snippets/fastcgi-php.conf;
>        fastcgi_pass unix:/run/php/php7.0-fpm.sock;
>    }

>    location ~ /\.ht {
>        deny all;
>    }
>}

When you've made the above changes, you can save and close the file.

Test your configuration file for syntax errors by typing:

>sudo nginx -t

If any errors are reported, go back and recheck your file before continuing.

When you are ready, reload Nginx to make the necessary changes:

> sudo systemctl reload nginx

## Step 4: Create a PHP File to Test Configuration
Your LEMP stack should now be completely set up. We can test it to validate that Nginx can correctly hand .php files off to our PHP processor.

We can do this by creating a test PHP file in our document root. Open a new file called info.php within your document root in your text editor:

> sudo vi /var/www/html/info.php

Type or paste the following lines into the new file. This is valid PHP code that will return information about our server:

/var/www/html/info.php

><?php
> phpinfo();
When you are finished, save and close the file.

Now, you can visit this page in your web browser by visiting your server's domain name or public IP address followed by /info.php:

http://server_domain_or_IP/info.php
