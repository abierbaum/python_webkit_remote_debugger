Goal
====
This project was created to help debug some webapps I wrote on iOS.  The problem was that the application would hard crash mobile safari but run fine on desktop browsers.  I needed a way to get a trace of the running application so I could see what was happening.  So I decided to see if I could get a dump from the remote debugger interface.

Thanks to also on stackoverflow [see herere](http://stackoverflow.com/questions/8599408/is-it-possible-to-connect-to-mobile-safari-remote-debugger-protocol-using-python) I think I can do it in python.  

So this project is the attempt to do just that.


References
==========
  * [websocket-client](https://github.com/liris/websocket-client): Python library we use
  * [Chrome Dev Tools: Remote Debugging](http://code.google.com/chrome/devtools/docs/remote-debugging.html): Reference for how to setup, use, and communicate with the debugger in Chrome.
