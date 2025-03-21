*Key implementation decisions

### Hosting Service

- **AWS S3**: Can host a [static website](https://docs.aws.amazon.com/AmazonS3/latest/userguide/HostingWebsiteOnS3Setup.html), but allows anonymous access only. For our needs, we require authorized user access for videos and scripts.
  
- **AWS EC2 free tier**:
  - Installed Nginx using [this guide](https://www.digitalocean.com/community/tutorials/how-to-install-nginx-on-ubuntu-20-04).
  - Enabled [Basic Authentication](https://www.digitalocean.com/community/tutorials/how-to-set-up-password-authentication-with-nginx-on-ubuntu-22-04).
  - [Script Editor](http://ec2-3-17-77-104.us-east-2.compute.amazonaws.com)  
  - Free Tier offers a maximum of 30GB storage.[Extend Storage](https://docs.aws.amazon.com/ebs/latest/userguide/recognize-expanded-volume-linux.html) 

### Video Player

- Initially attempted to use the YouTube Player Embed API since videos are uploaded as private. However, the API lacks an event to track playback position.
  
- Tested HTML5 video player. To implement:
  1. Enable MP4 streaming on the server side:
     - Install Nginx Extras with `sudo apt-get install nginx-extras`.
     - Add the following block:
     ```nginx
     location /data/video/ {
         mp4;
         mp4_buffer_size       1m;
         mp4_max_buffer_size   5m;
     }
     ```
     Note: `mp4_limit_rate` must be disabled as it's not supported in the free version of Nginx.
  
  2. For Chrome and Firefox compatibility, MP4 files need to be converted to H.264 formatdue to patent issues although this format is not required for Safari playback 

### Deployment
- The web site is under the web folder
- deploy.sh deploys the code. deploy_data.sh deploys data

### DNS and SSL
- Use [NoIP's dynamic DNS](https://my.noip.com/) - holylogos.servehttp.com
- [Enable SSL using Let's Encrypt](https://www.digitalocean.com/community/tutorials/how-to-secure-nginx-with-let-s-encrypt-on-ubuntu-22-04) 
- Tried Route 53. Unable to point registed domain to work

### Push to Test or Dev Site
- push_to_live.py
- source JunSSD/data
- test /Users/junyang/church/web/data
- production /opt/homebrew/var/www/church/web/data
- data copied :  config/sermon.json , script, script_patched
