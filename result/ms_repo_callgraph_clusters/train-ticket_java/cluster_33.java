// Cluster 33

// Node: preserveSuccess
package notification.controller;

import notification.entity.NotifyInfo;
import notification.mq.RabbitSend;
import notification.service.NotificationService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpHeaders;
import org.springframework.web.bind.annotation.*;

/**
 * @author Wenvi
 * @date 2017/6/15
 */
@RestController
@RequestMapping("/api/v1/notifyservice")
public class NotificationController {

    @Autowired
    NotificationService service;

    @Autowired
    RabbitSend sender;

    @Value("${test_send_mail_user}")
    String test_mail_user;

    @GetMapping(path = "/welcome")
    public String home() {
        return "Welcome to [ Notification Service ] !";
    }

    @GetMapping("/test_send_mq")
    public boolean test_send() {
        sender.send("test");
        return true;
    }

    @GetMapping("/test_send_mail")
    public boolean test_send_mail() {
        NotifyInfo notifyInfo = new NotifyInfo();
        notifyInfo.setDate("Wed Jul 21 09:49:44 CST 2021");
        notifyInfo.setEmail(test_mail_user);
        notifyInfo.setEndPlace("Test");
        notifyInfo.setStartPlace("Test");
        notifyInfo.setOrderNumber("111-111-111");
        notifyInfo.setPrice("100");
        notifyInfo.setSeatClass("1");
        notifyInfo.setSeatNumber("1102");
        notifyInfo.setStartTime("Sat May 04 07:00:00 CST 2013");
        notifyInfo.setUsername("h10g");

        service.preserveSuccess(notifyInfo, null);
        return true;
    }

    @PostMapping(value = "/notification/preserve_success")
    public boolean preserve_success(@RequestBody NotifyInfo info, @RequestHeader HttpHeaders headers) {
        return service.preserveSuccess(info, headers);
    }

    @PostMapping(value = "/notification/order_create_success")
    public boolean order_create_success(@RequestBody NotifyInfo info, @RequestHeader HttpHeaders headers) {
        return service.orderCreateSuccess(info, headers);
    }

    @PostMapping(value = "/notification/order_changed_success")
    public boolean order_changed_success(@RequestBody NotifyInfo info, @RequestHeader HttpHeaders headers) {
        return service.orderChangedSuccess(info, headers);
    }

    @PostMapping(value = "/notification/order_cancel_success")
    public boolean order_cancel_success(@RequestBody NotifyInfo info, @RequestHeader HttpHeaders headers) {
        return service.orderCancelSuccess(info, headers);
    }
}


// Node: preserve_success
// Node: order_create_success
// Node: orderCreateSuccess
// Node: order_changed_success
// Node: orderChangedSuccess
// Node: order_cancel_success
// Node: orderCancelSuccess
package notification.service;

import notification.entity.NotifyInfo;
import org.springframework.http.HttpHeaders;

/**
 * @author Wenvi
 * @date 2017/6/15
 */
public interface NotificationService {

    /**
     * preserve success with notify info
     *
     * @param info notify info
     * @param headers headers
     * @return boolean
     */
    boolean preserveSuccess(NotifyInfo info, HttpHeaders headers);

    /**S
     * order create success with notify info
     *
     * @param info notify info
     * @param headers headers
     * @return boolean
     */
    boolean orderCreateSuccess(NotifyInfo info, HttpHeaders headers);

    /**
     * order changed success with notify info
     *
     * @param info notify info
     * @param headers headers
     * @return boolean
     */
    boolean orderChangedSuccess(NotifyInfo info, HttpHeaders headers);

    /**
     * order cancel success with notify info
     *
     * @param info notify info
     * @param headers headers
     * @return boolean
     */
    boolean orderCancelSuccess(NotifyInfo info, HttpHeaders headers);
}


// Node: repos/cloned_ms_repos/train-ticket/ts-notification-service/src/main/java/notification/service/NotificationService.java:NotificationService.<init>
package notification.service;

import notification.entity.Mail;
import notification.entity.NotifyInfo;
import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.MockitoAnnotations;
import org.springframework.http.HttpHeaders;

@RunWith(JUnit4.class)
public class NotificationServiceImplTest {

    @InjectMocks
    private NotificationServiceImpl notificationServiceImpl;

    @Mock
    private MailService mailService;

    private HttpHeaders headers = new HttpHeaders();

    @Before
    public void setUp() {
        MockitoAnnotations.initMocks(this);
    }

    @Test
    public void testPreserveSuccess1() throws Exception {
        NotifyInfo info = new NotifyInfo();
        Mockito.doNothing().doThrow(new RuntimeException()).when(mailService).sendEmail(Mockito.any(Mail.class), Mockito.anyString());
        boolean result = notificationServiceImpl.preserveSuccess(info, headers);
        Assert.assertTrue(result);
    }

    @Test
    public void testPreserveSuccess2() throws Exception {
        NotifyInfo info = new NotifyInfo();
        Mockito.doThrow(new Exception()).when(mailService).sendEmail(Mockito.any(Mail.class), Mockito.anyString());
        boolean result = notificationServiceImpl.preserveSuccess(info, headers);
        Assert.assertFalse(result);
    }

    @Test
    public void testOrderCreateSuccess1() throws Exception {
        NotifyInfo info = new NotifyInfo();
        Mockito.doNothing().doThrow(new RuntimeException()).when(mailService).sendEmail(Mockito.any(Mail.class), Mockito.anyString());
        boolean result = notificationServiceImpl.orderCreateSuccess(info, headers);
        Assert.assertTrue(result);
    }

    @Test
    public void testOrderCreateSuccess2() throws Exception {
        NotifyInfo info = new NotifyInfo();
        Mockito.doThrow(new Exception()).when(mailService).sendEmail(Mockito.any(Mail.class), Mockito.anyString());
        boolean result = notificationServiceImpl.orderCreateSuccess(info, headers);
        Assert.assertFalse(result);
    }

    @Test
    public void testOrderChangedSuccess1() throws Exception {
        NotifyInfo info = new NotifyInfo();
        Mockito.doNothing().doThrow(new RuntimeException()).when(mailService).sendEmail(Mockito.any(Mail.class), Mockito.anyString());
        boolean result = notificationServiceImpl.orderChangedSuccess(info, headers);
        Assert.assertTrue(result);
    }

    @Test
    public void testOrderChangedSuccess2() throws Exception {
        NotifyInfo info = new NotifyInfo();
        Mockito.doThrow(new Exception()).when(mailService).sendEmail(Mockito.any(Mail.class), Mockito.anyString());
        boolean result = notificationServiceImpl.orderChangedSuccess(info, headers);
        Assert.assertFalse(result);
    }

    @Test
    public void testOrderCancelSuccess1() throws Exception {
        NotifyInfo info = new NotifyInfo();
        Mockito.doNothing().doThrow(new RuntimeException()).when(mailService).sendEmail(Mockito.any(Mail.class), Mockito.anyString());
        boolean result = notificationServiceImpl.orderCancelSuccess(info, headers);
        Assert.assertTrue(result);
    }

    @Test
    public void testOrderCancelSuccess2() throws Exception {
        NotifyInfo info = new NotifyInfo();
        Mockito.doThrow(new Exception()).when(mailService).sendEmail(Mockito.any(Mail.class), Mockito.anyString());
        boolean result = notificationServiceImpl.orderCancelSuccess(info, headers);
        Assert.assertFalse(result);
    }

}


// Node: testPreserveSuccess1
// Node: testPreserveSuccess2
// Node: Exception
// Node: testOrderCreateSuccess1
// Node: testOrderCreateSuccess2
// Node: testOrderChangedSuccess1
// Node: testOrderChangedSuccess2
// Node: testOrderCancelSuccess1
// Node: testOrderCancelSuccess2
