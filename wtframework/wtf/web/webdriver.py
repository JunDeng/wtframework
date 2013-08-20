##########################################################################
#This file is part of WTFramework. 
#
#    WTFramework is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    WTFramework is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with WTFramework.  If not, see <http://www.gnu.org/licenses/>.
##########################################################################

from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from wtframework.wtf.config import WTF_CONFIG_READER
from threading import current_thread



class WebDriverFactory(object):
    '''
    This class constructs a Selenium Webdriver using settings in the config file.
    
    Note: please be sure to uncomment the Unit test and run them manually before 
    pushing any changes.  This is because they are disabled.  The reason is 
    because the unit tests for this class can use up billable hours on sauce labs 
    or open annoying browser windows.
    '''

    # CONFIG SETTINGS #
    DRIVER_TYPE_CONFIG = "selenium.type"
    REMOTE_URL_CONFIG = "selenium.remote_url"
    BROWSER_TYPE_CONFIG = "selenium.browser"
    DESIRED_CAPABILITIES_CONFIG = "selenium.desired_capabilities"
    CHROME_DRIVER_PATH = "selenium.chromedriver_path"

    _DEFAULT_SELENIUM_SERVER_FOLDER = "selenium-server"

    # BROWSER CONSTANTS #
    HTMLUNIT = "HTMLUNIT"
    HTMLUNITWITHJS = "HTMLUNITWITHJS"
    ANDROID = "ANDROID"
    CHROME = "CHROME"
    FIREFOX = "FIREFOX"
    INTERNETEXPLORER = "INTERNETEXPLORER"
    IPAD = "IPAD"
    IPHONE = "IPHONE"
    OPERA = "OPERA"
    PHANTOMJS = "PHANTOMJS"
    SAFARI = "SAFARI"


    # Instance Variables#
    _config_reader = None


    def __init__(self, config_reader=None):
        '''
        Initializer.
        
        @param config_reader: Pass in a config reader if you want to stub this out.
        @type config_reader: ConfigReader
        '''

        if config_reader != None:
            self._config_reader = config_reader
        else:
            self._config_reader = WTF_CONFIG_READER



    def create_webdriver(self, testname=None):
        '''
            Creates an instance of Selenium webdriver based on config settings.
            This should only be called by a shutdown hook.  Do not call directly within 
            a test.
            
            @param testname: Optional test name to pass, this gets appended to the test name 
                             sent to selenium grid.

            @return: WebDriver
        '''
        try:
            driver_type = self._config_reader.get(WebDriverFactory.DRIVER_TYPE_CONFIG)
        except:
            print WebDriverFactory.DRIVER_TYPE_CONFIG + " setting is missing from config. Using defaults"
            driver_type = "LOCAL"

        if driver_type == "REMOTE":
            # Create desired capabilities.
            self.webdriver = self.__create_remote_webdriver_from_config(testname=testname)
        else:
            #handle as local webdriver
            self.webdriver = self.__create_driver_from_browser_config()

        self.webdriver.maximize_window()

        return self.webdriver



    def __create_driver_from_browser_config(self):
        '''
        Reads the config value for browser type.
        '''
        try:
            browser_type = self._config_reader.get(WebDriverFactory.BROWSER_TYPE_CONFIG)
        except KeyError:
            print WebDriverFactory.BROWSER_TYPE_CONFIG + " missing is missing from config file. Using defaults"
            browser_type = WebDriverFactory.FIREFOX

        browser_type_dict = {\
                             WebDriverFactory.CHROME: lambda:webdriver.Chrome(self._config_reader.get(WebDriverFactory.CHROME_DRIVER_PATH)),\
                             WebDriverFactory.FIREFOX: lambda:webdriver.Firefox(),\
                             WebDriverFactory.INTERNETEXPLORER: lambda:webdriver.Ie(),\
                             WebDriverFactory.OPERA:lambda:webdriver.Opera(),
                             WebDriverFactory.PHANTOMJS:lambda:webdriver.PhantomJS()}

        try:
            return browser_type_dict[browser_type]()
        except KeyError:
            raise TypeError("Unsupported Browser Type {0}".format(browser_type))
        # End of method.

    def __create_remote_webdriver_from_config(self, testname=None):
        '''
        Reads the config value for browser type.
        '''
        browser_type = self._config_reader.get(WebDriverFactory.BROWSER_TYPE_CONFIG)
        remote_url = self._config_reader.get(WebDriverFactory.REMOTE_URL_CONFIG)

        browser_constant_dict = {WebDriverFactory.HTMLUNIT:DesiredCapabilities.HTMLUNIT, \
                                 WebDriverFactory.HTMLUNITWITHJS:DesiredCapabilities.HTMLUNITWITHJS, \
                                 WebDriverFactory.ANDROID:DesiredCapabilities.ANDROID,\
                                 WebDriverFactory.CHROME:DesiredCapabilities.CHROME,\
                                 WebDriverFactory.FIREFOX:DesiredCapabilities.FIREFOX,\
                                 WebDriverFactory.INTERNETEXPLORER:DesiredCapabilities.INTERNETEXPLORER,\
                                 WebDriverFactory.IPAD:DesiredCapabilities.IPAD,\
                                 WebDriverFactory.IPHONE:DesiredCapabilities.IPHONE,\
                                 WebDriverFactory.OPERA:DesiredCapabilities.OPERA ,\
                                 WebDriverFactory.SAFARI:DesiredCapabilities.SAFARI,
                                 WebDriverFactory.PHANTOMJS:DesiredCapabilities.PHANTOMJS}

        try:
            desired_capabilities = browser_constant_dict[browser_type]
        except KeyError:
            raise TypeError("Unsupported Browser Type {0}".format(browser_type))

        # Get additional desired properties from config file and add them in.
        other_desired_capabilities = self._config_reader.get(WebDriverFactory.DESIRED_CAPABILITIES_CONFIG)

        for prop in other_desired_capabilities:
            value = other_desired_capabilities[prop]
            
            if type(other_desired_capabilities[prop]) is dict:
                #do some recursive call to flatten this setting.
                self.__flatten_capabilities(desired_capabilities, prop, other_desired_capabilities[prop])
            else: # Handle has a single string value.
                if isinstance(value, basestring):
                    desired_capabilities[prop] = value
                else:
                    desired_capabilities[prop] = str(value)

        # Set the test name property if specified in the WTF_TESTNAME var.
        try:
            test_name = self._config_reader.get("TESTNAME")
            desired_capabilities['name'] = test_name
        except KeyError:
            pass # No test name is specified, use the default.

        # Append optional testname postfix if supplied.
        if testname:
            desired_capabilities['name'] += "-" + testname
            
        # Instantiate remote webdriver.
        return webdriver.Remote(
            desired_capabilities = desired_capabilities,
            command_executor = remote_url
        )
        # End of method.

    def __flatten_capabilities(self, desired_capabilities, prefix, setting_group):
        for key in setting_group.keys():
            if type(setting_group[key]) is dict:
                # Do recursive call
                self.__flatten_capabilities(desired_capabilities, prefix + "." + key, setting_group[key])
            else:
                value = setting_group[key]
                if isinstance(value, basestring):
                    desired_capabilities[prefix + "." + key] = value
                else:
                    desired_capabilities[prefix + "." + key] = str(value)
        # End of method.



class WebDriverManager(object):
    '''
    Provides Singleton instance of Selenium WebDriver based on 
    config settings.
    
    Reason we don't make this a Utility class that provides a singleton 
    of the WebDriver itself is so we can allow that pice to be mocked 
    out to assist in unit testing framework classes that may use this. 
    '''
    
    "Config setting to reuse browser instances between WebdriverManager.new_driver() calls."
    REUSE_BROWSER = "selenium.reusebrowser"
    
    "Config setting to automatically tear down webdriver upon exiting the main script."
    SHUTDOWN_HOOK_CONFIG = "selenium.shutdown_hook"
    
    "Config setting to use new webdriver instance per thread."
    ENABLE_THREADING_SUPPORT = "selenium.threaded"


    def __init__(self, webdriver_factory=None, config=None):
        '''
        Initializer
        
        @param webdriver_factory: Optional webdriver factory to use to 
        create instances of webdriver.  This is useful for unit tests 
        that need to mock out the webdriver. 
        @type webdriver_factory: WebDriverFactory
        '''
        self.__webdriver = {} # Object with channel as a key
        self.__registered_drivers = {}
        
        if config:
            self.__config = config
        else:
            self.__config = WTF_CONFIG_READER
        
        if self.__config.get(WebDriverManager.SHUTDOWN_HOOK_CONFIG, True):
            self.__use_shutdown_hook = True
        else:
            self.__use_shutdown_hook = False
        
        if( webdriver_factory != None):
            self._webdriver_factory = webdriver_factory
        else:
            self._webdriver_factory = WebDriverFactory()



    def clean_up_webdrivers(self):
        '''
        Clean up webdrivers created during execution.
        '''
        # Quit webdrivers.
        print "WebdriverManager : Cleaning up webdrivers"
        try:
            if self.__use_shutdown_hook:
                for key in self.__registered_drivers.keys():
                    for driver in self.__registered_drivers[key]:
                        try:
                            print "Closing webdriver for thread: ", key
                            driver.quit()
                        except Exception as e:
                            print e
        except:
            pass


    def close_driver(self):
        """
        Close current instance of webdriver.
        """
        channel = self.__get_channel()
        driver = self.__get_driver_for_channel(channel)
        if self.__config.get(WebDriverManager.REUSE_BROWSER, True):
            #If reuse browser is set, we'll avoid closing it and just clear out the cookies,
            # and reset the location.
            try:
                driver.delete_all_cookies()
                driver.get("about:blank") #check to see if webdriver is still responding
            except:
                pass
        
        if driver is not None:
            try:
                driver.quit()
            except:
                pass

            self.__unregister_driver(channel)
            if driver in self.__registered_drivers[channel]:
                self.__registered_drivers[channel].remove(driver)

            self.webdriver = None



    def get_driver(self):
        '''
        Get an already running instance of webdriver. If there is none, it will create one.
        @return: Selenium WebDriver instance.
        @rtype: WebDriver
        '''
        driver = self.__get_driver_for_channel(self.__get_channel())
        if driver is None:
            driver = self.new_driver()

        return driver



    def is_driver_available(self):
        '''
        Check if a webdriver instance is created.
        @rtype: bool
        '''
        channel = self.__get_channel()
        try:
            return self.__webdriver[channel] != None
        except:
            return False


    def new_driver(self, testname=None):
        '''
        Used at a start of a test to get a new instance of webdriver.  If the 
        'resuebrowser' setting is true, it will use a recycled webdriver instance.
        @return: Selenium WebDriver instance.
        @rtype: WebDriver
        '''
        channel = self.__get_channel()

        # Get reference for the current driver.
        driver = self.__get_driver_for_channel(channel)
        
        if self.__config.get(WebDriverManager.REUSE_BROWSER, True):
            
            if driver is None:
                driver = self._webdriver_factory.create_webdriver(testname=testname)

                #Register webdriver so it can be retrieved by the manager and cleaned up after exit.
                self.__register_driver(channel, driver)
            else:
                try:
                    # Attempt to get the browser to a pristine state as possible when we are 
                    # reusing this for another test.
                    driver.delete_all_cookies()
                    driver.get("about:blank") #check to see if webdriver is still responding
                except:
                    # In the case the browser is unhealthy, we should kill it and serve a new one.
                    try:
                        if driver.is_online():
                            driver.quit()
                    except:
                        pass

                    driver = self._webdriver_factory.create_webdriver(testname=testname)
                    self.__register_driver(channel, driver)
                
        else:
            # Attempt to tear down any existing webdriver.
            if driver is not None:
                try:
                    driver.quit()
                except:
                    pass
            self.__unregister_driver(channel)
            driver = self._webdriver_factory.create_webdriver(testname=testname)
            self.__register_driver(channel, driver)

        return driver
        # End of new_driver method.

    def __register_driver(self, channel, webdriver):
        "Register webdriver to a channel."
        
        # Add to list of webdrivers to cleanup.
        if not self.__registered_drivers.has_key(channel):
            self.__registered_drivers[channel] = [] #set to new empty array

        self.__registered_drivers[channel].append(webdriver)

        # Set singleton instance for the channel
        self.__webdriver[channel] = webdriver

    def __unregister_driver(self, channel):
        "Unregister webdriver"
        driver = self.__get_driver_for_channel(channel)
        
        if self.__registered_drivers.has_key(channel) \
        and driver in self.__registered_drivers[channel]:

            self.__registered_drivers[channel].remove(driver)

        self.__webdriver[channel] = None


    def __get_driver_for_channel(self, channel):
        "Get webdriver for channel"
        try:
            return self.__webdriver[channel]
        except:
            return None


    def __get_channel(self):
        "Get the channel to register webdriver to."
        if self.__config.get(WebDriverManager.ENABLE_THREADING_SUPPORT, False):
            channel = current_thread().ident
        else:
            channel = 0
        
        return channel


    def __del__(self):
        "Deconstructor, call cleanup drivers."
        try:
            self.clean_up_webdrivers()
        except:
            pass


# Global Instance of WebDriver Manager
WTF_WEBDRIVER_MANAGER = WebDriverManager()


