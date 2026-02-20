// Cluster 52

package inside_payment.util;

import javax.servlet.http.Cookie;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import java.util.HashMap;
import java.util.Map;

/**
 * @author fdse
 */
public class CookieUtil {

    private CookieUtil() {
        throw new IllegalStateException("Utility class");
    }

    public static void addCookie(HttpServletResponse response, String name, String value, int maxAge){
        Cookie cookie = new Cookie(name,value);
        // against Cross-Site Scripting (XSS) attacks
        cookie.setHttpOnly(true);
        cookie.setPath("/");
        if(maxAge>0) {
            cookie.setMaxAge(maxAge);
        }
        response.addCookie(cookie);
    }

    public static Cookie getCookieByName(HttpServletRequest request, String name){
        Map<String,Cookie> cookieMap = readCookieMap(request);
        if(cookieMap.containsKey(name)){
            return cookieMap.get(name);
        }else{
            return null;
        }
    }

    private static Map<String,Cookie> readCookieMap(HttpServletRequest request){
        Map<String,Cookie> cookieMap = new HashMap<>();
        Cookie[] cookies = request.getCookies();
        if(null!=cookies){
            for(Cookie cookie : cookies){
                cookieMap.put(cookie.getName(), cookie);
            }
        }
        return cookieMap;
    }
}


// Node: addCookie
// Node: Cookie
// Node: Scripting
// Node: setHttpOnly
// Node: setPath
// Node: setMaxAge
// Node: getCookieByName
// Node: readCookieMap
// Node: getCookies
package verifycode.service.impl;

import com.google.common.cache.Cache;
import com.google.common.cache.CacheBuilder;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpHeaders;
import org.springframework.stereotype.Service;
import verifycode.service.VerifyCodeService;
import verifycode.util.CookieUtil;

import javax.servlet.http.Cookie;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import java.awt.*;
import java.awt.image.BufferedImage;
import java.io.OutputStream;
import java.util.HashMap;
import java.util.Map;
import java.util.Random;
import java.util.UUID;
import java.util.concurrent.TimeUnit;

/**
 * @author fdse
 */
@Service
public class VerifyCodeServiceImpl implements VerifyCodeService {

    public static final int CAPTCHA_EXPIRED = 1000;
    private static final Logger LOGGER = LoggerFactory.getLogger(VerifyCodeServiceImpl.class);

    String ysbCaptcha = "YsbCaptcha";

    /**
     * build local cache
     */
    public Cache<String, String> cacheCode = CacheBuilder.newBuilder()
            // max  size
            .maximumSize(CAPTCHA_EXPIRED)
            .expireAfterAccess(CAPTCHA_EXPIRED, TimeUnit.SECONDS)
            .build();

    private static char mapTable[] = {
            'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J',
            'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W',
            'X', 'Y', 'Z', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9'};

    @Override
    public Map<String, Object> getImageCode(int width, int height, OutputStream os, HttpServletRequest request, HttpServletResponse response, HttpHeaders headers) {
        Map<String, Object> returnMap = new HashMap<>();
        if (width <= 0) {
            width = 60;
        }
        if (height <= 0) {
            height = 20;
        }
        BufferedImage image = new BufferedImage(width, height, BufferedImage.TYPE_INT_RGB);

        Graphics g = image.getGraphics();

        Random random = new Random(); //NOSONAR

        g.setColor(getRandColor(200, 250));
        g.fillRect(0, 0, width, height);

        g.setFont(new Font("Times New Roman", Font.PLAIN, 18));

        g.setColor(getRandColor(160, 200));
        for (int i = 0; i < 168; i++) {
            int x = random.nextInt(width);
            int y = random.nextInt(height);
            int xl = random.nextInt(12);
            int yl = random.nextInt(12);
            g.drawLine(x, y, x + xl, y + yl);
        }

        String strEnsure = "";

        for (int i = 0; i < 4; ++i) {
            strEnsure += mapTable[(int) (mapTable.length * Math.random())];

            g.setColor(new Color(20 + random.nextInt(110), 20 + random.nextInt(110), 20 + random.nextInt(110)));

            String str = strEnsure.substring(i, i + 1);
            g.drawString(str, 13 * i + 6, 16);
        }

        g.dispose();
        returnMap.put("image", image);
        returnMap.put("strEnsure", strEnsure);

        Cookie cookie = CookieUtil.getCookieByName(request, ysbCaptcha);
        String cookieId;
        if (cookie == null) {
            VerifyCodeServiceImpl.LOGGER.warn("[getImageCode][Get image code warn.Cookie not found][Path Info: {}]",request.getPathInfo());
            cookieId = UUID.randomUUID().toString().replace("-", "").toUpperCase();
            CookieUtil.addCookie(response, ysbCaptcha, cookieId, CAPTCHA_EXPIRED);
        } else {
            if (cookie.getValue() != null) {
                cookieId = UUID.randomUUID().toString().replace("-", "").toUpperCase();
                CookieUtil.addCookie(response, ysbCaptcha, cookieId, CAPTCHA_EXPIRED);
            } else {
                cookieId = cookie.getValue();
            }
        }
        VerifyCodeServiceImpl.LOGGER.info("[getImageCode][strEnsure: {}]", strEnsure);
        cacheCode.put(cookieId, strEnsure);
        return returnMap;
    }

    @Override
    public boolean verifyCode(HttpServletRequest request, HttpServletResponse response, String receivedCode, HttpHeaders headers) {
        boolean result = false;
        Cookie cookie = CookieUtil.getCookieByName(request, ysbCaptcha);
        String cookieId;
        if (cookie == null) {
            VerifyCodeServiceImpl.LOGGER.warn("[verifyCode][Verify code warn][Cookie not found][Path Info: {}]",request.getPathInfo());
            cookieId = UUID.randomUUID().toString().replace("-", "").toUpperCase();
            CookieUtil.addCookie(response, ysbCaptcha, cookieId, CAPTCHA_EXPIRED);
        } else {
            cookieId = cookie.getValue();
        }

        String code = cacheCode.getIfPresent(cookieId);
        LOGGER.info("GET Code By cookieId " + cookieId + "   is :" + code);
        if (code == null) {
            VerifyCodeServiceImpl.LOGGER.warn("[verifyCode][Get image code warn][Code not found][CookieId: {}]",cookieId);
            return false;
        }
        if (code.equalsIgnoreCase(receivedCode)) {
            result = true;
        }
        return result;
    }


    static Color getRandColor(int fc, int bc) {
        Random random = new Random(); //NOSONAR
        if (fc > 255) {
            fc = 255;
        }
        if (bc > 255) {
            bc = 255;
        }
        int r = fc + random.nextInt(bc - fc);
        int g = fc + random.nextInt(bc - fc);
        int b = fc + random.nextInt(bc - fc);
        return new Color(r, g, b);
    }

}


// Node: BufferedImage
// Node: getGraphics
// Node: setColor
// Node: getRandColor
// Node: fillRect
// Node: setFont
// Node: Font
// Node: drawLine
// Node: random
// Node: Color
// Node: drawString
// Node: dispose
// Node: getPathInfo
// Node: toUpperCase
// Node: getIfPresent
// Node: equalsIgnoreCase
package verifycode.util;

import javax.servlet.http.Cookie;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import java.util.HashMap;
import java.util.Map;

/**
 * @author fdse
 */
public class CookieUtil {

    private CookieUtil() {
        throw new IllegalStateException("Utility class");
    }

    public static void addCookie(HttpServletResponse response, String name, String value, int maxAge){
        Cookie cookie = new Cookie(name,value);
        // against Cross-Site Scripting (XSS) attacks.
        cookie.setHttpOnly(true);
        cookie.setPath("/");
        if(maxAge>0) {
            cookie.setMaxAge(maxAge);
        }
        response.addCookie(cookie);
    }

    public static Cookie getCookieByName(HttpServletRequest request, String name){
        Map<String,Cookie> cookieMap = readCookieMap(request);
        return cookieMap.getOrDefault(name, null);
    }

    private static Map<String,Cookie> readCookieMap(HttpServletRequest request){
        Map<String,Cookie> cookieMap = new HashMap<>();
        Cookie[] cookies = request.getCookies();
        if(null!=cookies){
            for(Cookie cookie : cookies){
                cookieMap.put(cookie.getName(), cookie);
            }
        }
        return cookieMap;
    }
}


// Node: getOrDefault
package verifycode.service;

import org.junit.Assert;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;
import org.springframework.http.HttpHeaders;
import verifycode.service.impl.VerifyCodeServiceImpl;

import javax.servlet.*;
import javax.servlet.http.*;
import java.io.*;
import java.security.Principal;
import java.util.Collection;
import java.util.Enumeration;
import java.util.Locale;
import java.util.Map;

@RunWith(JUnit4.class)
public class VerifyCodeServiceImplTest {

    private VerifyCodeServiceImpl verifyCodeServiceImpl = new VerifyCodeServiceImpl();
    private HttpHeaders headers = new HttpHeaders();

    private HttpServletRequest request = new HttpServletRequest() {
        @Override
        public String getAuthType() {
            return null;
        }

        @Override
        public Cookie[] getCookies() {
            return new Cookie[0];
        }

        @Override
        public long getDateHeader(String s) {
            return 0;
        }

        @Override
        public String getHeader(String s) {
            return null;
        }

        @Override
        public Enumeration<String> getHeaders(String s) {
            return null;
        }

        @Override
        public Enumeration<String> getHeaderNames() {
            return null;
        }

        @Override
        public int getIntHeader(String s) {
            return 0;
        }

        @Override
        public String getMethod() {
            return null;
        }

        @Override
        public String getPathInfo() {
            return null;
        }

        @Override
        public String getPathTranslated() {
            return null;
        }

        @Override
        public String getContextPath() {
            return null;
        }

        @Override
        public String getQueryString() {
            return null;
        }

        @Override
        public String getRemoteUser() {
            return null;
        }

        @Override
        public boolean isUserInRole(String s) {
            return false;
        }

        @Override
        public Principal getUserPrincipal() {
            return null;
        }

        @Override
        public String getRequestedSessionId() {
            return null;
        }

        @Override
        public String getRequestURI() {
            return null;
        }

        @Override
        public StringBuffer getRequestURL() {
            return null;
        }

        @Override
        public String getServletPath() {
            return null;
        }

        @Override
        public HttpSession getSession(boolean b) {
            return null;
        }

        @Override
        public HttpSession getSession() {
            return null;
        }

        @Override
        public String changeSessionId() {
            return null;
        }

        @Override
        public boolean isRequestedSessionIdValid() {
            return false;
        }

        @Override
        public boolean isRequestedSessionIdFromCookie() {
            return false;
        }

        @Override
        public boolean isRequestedSessionIdFromURL() {
            return false;
        }

        @Override
        public boolean isRequestedSessionIdFromUrl() {
            return false;
        }

        @Override
        public boolean authenticate(HttpServletResponse httpServletResponse) throws IOException, ServletException {
            return false;
        }

        @Override
        public void login(String s, String s1) throws ServletException {

        }

        @Override
        public void logout() throws ServletException {

        }

        @Override
        public Collection<Part> getParts() throws IOException, ServletException {
            return null;
        }

        @Override
        public Part getPart(String s) throws IOException, ServletException {
            return null;
        }

        @Override
        public <T extends HttpUpgradeHandler> T upgrade(Class<T> aClass) throws IOException, ServletException {
            return null;
        }

        @Override
        public Object getAttribute(String s) {
            return null;
        }

        @Override
        public Enumeration<String> getAttributeNames() {
            return null;
        }

        @Override
        public String getCharacterEncoding() {
            return null;
        }

        @Override
        public void setCharacterEncoding(String s) throws UnsupportedEncodingException {

        }

        @Override
        public int getContentLength() {
            return 0;
        }

        @Override
        public long getContentLengthLong() {
            return 0;
        }

        @Override
        public String getContentType() {
            return null;
        }

        @Override
        public ServletInputStream getInputStream() throws IOException {
            return null;
        }

        @Override
        public String getParameter(String s) {
            return null;
        }

        @Override
        public Enumeration<String> getParameterNames() {
            return null;
        }

        @Override
        public String[] getParameterValues(String s) {
            return new String[0];
        }

        @Override
        public Map<String, String[]> getParameterMap() {
            return null;
        }

        @Override
        public String getProtocol() {
            return null;
        }

        @Override
        public String getScheme() {
            return null;
        }

        @Override
        public String getServerName() {
            return null;
        }

        @Override
        public int getServerPort() {
            return 0;
        }

        @Override
        public BufferedReader getReader() throws IOException {
            return null;
        }

        @Override
        public String getRemoteAddr() {
            return null;
        }

        @Override
        public String getRemoteHost() {
            return null;
        }

        @Override
        public void setAttribute(String s, Object o) {

        }

        @Override
        public void removeAttribute(String s) {

        }

        @Override
        public Locale getLocale() {
            return null;
        }

        @Override
        public Enumeration<Locale> getLocales() {
            return null;
        }

        @Override
        public boolean isSecure() {
            return false;
        }

        @Override
        public RequestDispatcher getRequestDispatcher(String s) {
            return null;
        }

        @Override
        public String getRealPath(String s) {
            return null;
        }

        @Override
        public int getRemotePort() {
            return 0;
        }

        @Override
        public String getLocalName() {
            return null;
        }

        @Override
        public String getLocalAddr() {
            return null;
        }

        @Override
        public int getLocalPort() {
            return 0;
        }

        @Override
        public ServletContext getServletContext() {
            return null;
        }

        @Override
        public AsyncContext startAsync() throws IllegalStateException {
            return null;
        }

        @Override
        public AsyncContext startAsync(ServletRequest servletRequest, ServletResponse servletResponse) throws IllegalStateException {
            return null;
        }

        @Override
        public boolean isAsyncStarted() {
            return false;
        }

        @Override
        public boolean isAsyncSupported() {
            return false;
        }

        @Override
        public AsyncContext getAsyncContext() {
            return null;
        }

        @Override
        public DispatcherType getDispatcherType() {
            return null;
        }
    };
    private HttpServletResponse response = new HttpServletResponse() {
        @Override
        public void addCookie(Cookie cookie) {

        }

        @Override
        public boolean containsHeader(String s) {
            return false;
        }

        @Override
        public String encodeURL(String s) {
            return null;
        }

        @Override
        public String encodeRedirectURL(String s) {
            return null;
        }

        @Override
        public String encodeUrl(String s) {
            return null;
        }

        @Override
        public String encodeRedirectUrl(String s) {
            return null;
        }

        @Override
        public void sendError(int i, String s) throws IOException {

        }

        @Override
        public void sendError(int i) throws IOException {

        }

        @Override
        public void sendRedirect(String s) throws IOException {

        }

        @Override
        public void setDateHeader(String s, long l) {

        }

        @Override
        public void addDateHeader(String s, long l) {

        }

        @Override
        public void setHeader(String s, String s1) {

        }

        @Override
        public void addHeader(String s, String s1) {

        }

        @Override
        public void setIntHeader(String s, int i) {

        }

        @Override
        public void addIntHeader(String s, int i) {

        }

        @Override
        public void setStatus(int i) {

        }

        @Override
        public void setStatus(int i, String s) {

        }

        @Override
        public int getStatus() {
            return 0;
        }

        @Override
        public String getHeader(String s) {
            return null;
        }

        @Override
        public Collection<String> getHeaders(String s) {
            return null;
        }

        @Override
        public Collection<String> getHeaderNames() {
            return null;
        }

        @Override
        public String getCharacterEncoding() {
            return null;
        }

        @Override
        public String getContentType() {
            return null;
        }

        @Override
        public ServletOutputStream getOutputStream() throws IOException {
            return null;
        }

        @Override
        public PrintWriter getWriter() throws IOException {
            return null;
        }

        @Override
        public void setCharacterEncoding(String s) {

        }

        @Override
        public void setContentLength(int i) {

        }

        @Override
        public void setContentLengthLong(long l) {

        }

        @Override
        public void setContentType(String s) {

        }

        @Override
        public void setBufferSize(int i) {

        }

        @Override
        public int getBufferSize() {
            return 0;
        }

        @Override
        public void flushBuffer() throws IOException {

        }

        @Override
        public void resetBuffer() {

        }

        @Override
        public boolean isCommitted() {
            return false;
        }

        @Override
        public void reset() {

        }

        @Override
        public void setLocale(Locale locale) {

        }

        @Override
        public Locale getLocale() {
            return null;
        }
    };

    @Test
    public void testGetImageCode() {
        OutputStream os = System.out;
        Map<String, Object> returnMap = verifyCodeServiceImpl.getImageCode(60, 20, os, request, response, headers);
        Assert.assertNotNull(returnMap);
        Assert.assertNotNull(returnMap.get("strEnsure"));
    }

    @Test
    public void testVerifyCode() {
        boolean result = verifyCodeServiceImpl.verifyCode(request, response, "XYZ5", headers);
        Assert.assertFalse(result);
    }

}




package org.myproject.ms.monitoring;

import java.util.Collection;
import java.util.LinkedHashSet;

import org.springframework.boot.context.properties.ConfigurationProperties;


@ConfigurationProperties("spring.sleuth.keys")
public class ChainKeys {

	private Http http = new Http();

	private Message message = new Message();

	private Hystrix hystrix = new Hystrix();

	private Async async = new Async();

	private Mvc mvc = new Mvc();

	public Http getHttp() {
		return this.http;
	}

	public Message getMessage() {
		return this.message;
	}

	public Hystrix getHystrix() {
		return this.hystrix;
	}

	public Async getAsync() {
		return this.async;
	}

	public Mvc getMvc() {
		return this.mvc;
	}

	public void setHttp(Http http) {
		this.http = http;
	}

	public void setMessage(Message message) {
		this.message = message;
	}

	public void setHystrix(Hystrix hystrix) {
		this.hystrix = hystrix;
	}

	public void setAsync(Async async) {
		this.async = async;
	}

	public void setMvc(Mvc mvc) {
		this.mvc = mvc;
	}

	public static class Message {

		private Payload payload = new Payload();

		public Payload getPayload() {
			return this.payload;
		}

		public String getPrefix() {
			return this.prefix;
		}

		public Collection<String> getHeaders() {
			return this.headers;
		}

		public void setPayload(Payload payload) {
			this.payload = payload;
		}

		public void setPrefix(String prefix) {
			this.prefix = prefix;
		}

		public void setHeaders(Collection<String> headers) {
			this.headers = headers;
		}

		public static class Payload {
			
			private String size = "message/payload-size";
			
			private String type = "message/payload-type";

			public String getSize() {
				return this.size;
			}

			public String getType() {
				return this.type;
			}

			public void setSize(String size) {
				this.size = size;
			}

			public void setType(String type) {
				this.type = type;
			}
		}

		
		private String prefix = "message/";

		
		private Collection<String> headers = new LinkedHashSet<String>();

	}

	public static class Http {

		
		private String host = "http.host";

		
		private String method = "http.method";

		
		private String path = "http.path";

		
		private String url = "http.url";

		
		private String statusCode = "http.status_code";

		
		private String requestSize = "http.request.size";

		
		private String responseSize = "http.response.size";

		
		private String prefix = "http.";

		
		private Collection<String> headers = new LinkedHashSet<String>();

		public String getHost() {
			return this.host;
		}

		public String getMethod() {
			return this.method;
		}

		public String getPath() {
			return this.path;
		}

		public String getUrl() {
			return this.url;
		}

		public String getStatusCode() {
			return this.statusCode;
		}

		public String getRequestSize() {
			return this.requestSize;
		}

		public String getResponseSize() {
			return this.responseSize;
		}

		public String getPrefix() {
			return this.prefix;
		}

		public Collection<String> getHeaders() {
			return this.headers;
		}

		public void setHost(String host) {
			this.host = host;
		}

		public void setMethod(String method) {
			this.method = method;
		}

		public void setPath(String path) {
			this.path = path;
		}

		public void setUrl(String url) {
			this.url = url;
		}

		public void setStatusCode(String statusCode) {
			this.statusCode = statusCode;
		}

		public void setRequestSize(String requestSize) {
			this.requestSize = requestSize;
		}

		public void setResponseSize(String responseSize) {
			this.responseSize = responseSize;
		}

		public void setPrefix(String prefix) {
			this.prefix = prefix;
		}

		public void setHeaders(Collection<String> headers) {
			this.headers = headers;
		}
	}

	
	public static class Hystrix {

		
		private String prefix = "";

		
		private String commandKey = "commandKey";

		
		private String commandGroup = "commandGroup";

		
		private String threadPoolKey = "threadPoolKey";

		public String getPrefix() {
			return this.prefix;
		}

		public String getCommandKey() {
			return this.commandKey;
		}

		public String getCommandGroup() {
			return this.commandGroup;
		}

		public String getThreadPoolKey() {
			return this.threadPoolKey;
		}

		public void setPrefix(String prefix) {
			this.prefix = prefix;
		}

		public void setCommandKey(String commandKey) {
			this.commandKey = commandKey;
		}

		public void setCommandGroup(String commandGroup) {
			this.commandGroup = commandGroup;
		}

		public void setThreadPoolKey(String threadPoolKey) {
			this.threadPoolKey = threadPoolKey;
		}
	}

	
	public static class Async {

		
		private String prefix = "";

		
		private String threadNameKey = "thread";

		
		private String classNameKey = "class";

		
		private String methodNameKey = "method";

		public String getPrefix() {
			return this.prefix;
		}

		public String getThreadNameKey() {
			return this.threadNameKey;
		}

		public String getClassNameKey() {
			return this.classNameKey;
		}

		public String getMethodNameKey() {
			return this.methodNameKey;
		}

		public void setPrefix(String prefix) {
			this.prefix = prefix;
		}

		public void setThreadNameKey(String threadNameKey) {
			this.threadNameKey = threadNameKey;
		}

		public void setClassNameKey(String classNameKey) {
			this.classNameKey = classNameKey;
		}

		public void setMethodNameKey(String methodNameKey) {
			this.methodNameKey = methodNameKey;
		}
	}

	
	public static class Mvc {

		
		private String controllerClass = "mvc.controller.class";

		
		private String controllerMethod = "mvc.controller.method";

		public String getControllerClass() {
			return this.controllerClass;
		}

		public void setControllerClass(String controllerClass) {
			this.controllerClass = controllerClass;
		}

		public String getControllerMethod() {
			return this.controllerMethod;
		}

		public void setControllerMethod(String controllerMethod) {
			this.controllerMethod = controllerMethod;
		}
	}

}


