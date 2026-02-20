// Cluster 39

package net.javaguides.order_service.paypal;

import lombok.RequiredArgsConstructor;
import org.json.JSONArray;
import org.json.JSONObject;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.Base64;

@Service
@RequiredArgsConstructor
public class PayPalService {

    @Value("${paypal.client-id}")
    public static String CLIENT_ID;

    @Value("${paypal.client-secret}")
    public static String CLIENT_SECRET;

    private static final String PAYPAL_API = "https://api.sandbox.paypal.com/v2/checkout/orders/";
    //*
    public void refundPayment(String captureId) {
       try {
           URL url = new URL("https://api.sandbox.paypal.com/v2/payments/captures/" + captureId + "/refund");
           int responseCode = getResponseCode(url);
           if (responseCode != HttpURLConnection.HTTP_CREATED) {
               throw new RuntimeException("Refund failed with response code: " + responseCode);
           }
       }catch(Exception e){
           throw new RuntimeException("Refund failed: " + e.getMessage());
       }
    }

    public String getCaptureIdFromOrder(String orderId) throws Exception {
        URL url = new URL(PAYPAL_API + orderId);
        HttpURLConnection connection = (HttpURLConnection) url.openConnection();
        connection.setRequestMethod("GET");
        connection.setRequestProperty("Authorization", "Bearer " + getAccessToken());
        connection.setRequestProperty("Content-Type", "application/json");

        int responseCode = connection.getResponseCode();
        if (responseCode == HttpURLConnection.HTTP_OK) {
            try (BufferedReader br = new BufferedReader(new InputStreamReader(connection.getInputStream(), "utf-8"))) {
                StringBuilder response = new StringBuilder();
                String responseLine;
                while ((responseLine = br.readLine()) != null) {
                    response.append(responseLine.trim());
                }

                JSONObject jsonResponse = new JSONObject(response.toString());

                JSONArray purchaseUnits = jsonResponse.getJSONArray("purchase_units");
                JSONObject payments = purchaseUnits.getJSONObject(0).getJSONObject("payments");
                if (payments.has("captures")) {
                    JSONArray captures = payments.getJSONArray("captures");
                    for (int i = 0; i < captures.length(); i++) {
                        JSONObject capture = captures.getJSONObject(i);
                        String status = capture.getString("status");
                        if ("COMPLETED".equals(status)) {
                            return capture.getString("id");
                        }
                    }
                }
            }
        } else {
            throw new RuntimeException("Failed to retrieve order details from PayPal.");
        }
        return null;
    }

    private int getResponseCode(URL url) throws Exception {
        HttpURLConnection connection = (HttpURLConnection) url.openConnection();
        connection.setRequestMethod("POST");
        connection.setRequestProperty("Content-Type", "application/json");
        connection.setRequestProperty("Authorization", "Bearer " + getAccessToken());
        connection.setDoOutput(true);

        try (OutputStream os = connection.getOutputStream()) {
            byte[] input = "{}".getBytes("utf-8");
            os.write(input, 0, input.length);
        }

        return connection.getResponseCode();
    }

    // Lấy access token
    private String getAccessToken() throws Exception {
        URL url = new URL("https://api-m.sandbox.paypal.com/v1/oauth2/token");
        String credentials = CLIENT_ID + ":" + CLIENT_SECRET;
        String authHeader = "Basic " + Base64.getEncoder().encodeToString(credentials.getBytes());

        HttpURLConnection connection = (HttpURLConnection) url.openConnection();
        connection.setRequestMethod("POST");
        connection.setRequestProperty("Authorization", authHeader);
        connection.setRequestProperty("Content-Type", "application/x-www-form-urlencoded");
        connection.setDoOutput(true);

        try (OutputStream os = connection.getOutputStream()) {
            String params = "grant_type=client_credentials";
            os.write(params.getBytes("utf-8"));
        }

        int responseCode = connection.getResponseCode();
        if (responseCode == HttpURLConnection.HTTP_OK) {
            try (BufferedReader br = new BufferedReader(new InputStreamReader(connection.getInputStream(), "utf-8"))) {
                StringBuilder response = new StringBuilder();
                String responseLine;
                while ((responseLine = br.readLine()) != null) {
                    response.append(responseLine.trim());
                }
                JSONObject jsonResponse = new JSONObject(response.toString());
                return jsonResponse.getString("access_token");
            }
        } else {
            throw new RuntimeException("Failed to get access token.");
        }
    }
}


// Node: URL
// Node: getResponseCode
// Node: getCaptureIdFromOrder
// Node: openConnection
// Node: setRequestMethod
// Node: setRequestProperty
// Node: getAccessToken
// Node: try
// Node: BufferedReader
// Node: InputStreamReader
// Node: getInputStream
// Node: StringBuilder
// Node: readLine
// Node: append
// Node: trim
// Node: JSONObject
// Node: getJSONArray
// Node: getJSONObject
// Node: has
// Node: length
// Node: getString
// Node: setDoOutput
// Node: getOutputStream
// Node: getEncoder
// Node: encodeToString
package net.javaguides.email_service.service;

import jakarta.mail.MessagingException;
import jakarta.mail.internet.MimeMessage;
import net.javaguides.common_lib.dto.ApiResponse;
import net.javaguides.common_lib.dto.order.OrderEvent;
import net.javaguides.common_lib.dto.order.OrderItemDTO;
import net.javaguides.email_service.dto.ProductStockResponse;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.core.io.ClassPathResource;
import org.springframework.mail.javamail.JavaMailSender;
import org.springframework.mail.javamail.MimeMessageHelper;
import org.springframework.stereotype.Service;
import org.springframework.scheduling.annotation.Async;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.math.BigDecimal;
import java.nio.charset.StandardCharsets;
import java.text.NumberFormat;
import java.util.Date;
import java.util.List;
import java.util.Locale;
import java.util.Map;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

@Service
public class EmailService {

    @Autowired
    private JavaMailSender mailSender;

    @Autowired
    private ProductAPIClient productClient;
    private static final Logger logger = LoggerFactory.getLogger(EmailService.class);



    /**
     * Sends an order confirmation email by loading the HTML template and replacing placeholders.
     *
     * @param order The order details
     * @throws MessagingException if sending fails
     * @throws IOException if template reading fails
     */
    public void sendOrderConfirmationEmail(OrderEvent order)
            throws MessagingException, IOException {
        try {
            // Load the HTML template from resources
            String template = loadTemplate("templates/email-template.html");

            // Fetch detailed product information for each OrderItem
            List<OrderItemDTO> items = order.getOrderDTO().getOrderItems();
            StringBuilder orderItemsHtmlBuilder = new StringBuilder();
            BigDecimal amount = BigDecimal.valueOf(0);

            NumberFormat currencyFormatter = NumberFormat.getCurrencyInstance(Locale.US);

            for(OrderItemDTO item : items){
                try {
                    ApiResponse<ProductStockResponse> productResponse = productClient.getProductById(item.getProductId()).getBody();


                    if(productResponse != null && productResponse.getStatusCode() != 200){
                        logger.warn("Product with ID {} not found.", item.getProductId());
                        return;
                    }


                    BigDecimal totalPrice = productResponse.getData().getProduct().getPrice().multiply(BigDecimal.valueOf(item.getQuantity()));

                    amount = amount.add(totalPrice);

                    String formattedUnitPrice = currencyFormatter.format(productResponse.getData().getProduct().getPrice());
                    String formattedTotalPrice = currencyFormatter.format(totalPrice);

                    orderItemsHtmlBuilder.append("<tr>")
                            .append("<td><img width='100' height='100' src='").append(productResponse.getData().getProduct().getImageUrl()).append("' alt='Product Image'/></td>")
                            .append("<td>").append(productResponse.getData().getProduct().getName()).append("</td>")
                            .append("<td>").append(item.getQuantity()).append("</td>")
                            .append("<td>").append(formattedUnitPrice).append("</td>")
                            .append("<td>").append(formattedTotalPrice).append("</td>")
                            .append("</tr>");

                } catch (Exception e) {
                    logger.error("Error fetching product with ID {}: {}", item.getProductId(), e.getMessage());
                    // Optionally, you can continue or rethrow the exception based on requirements
                    continue;
                }
            }

            String orderItemsHtml = orderItemsHtmlBuilder.toString();
            String formattedGrandTotal = currencyFormatter.format(amount);

            // Prepare variables for template replacement
            Map<String, String> variables = Map.of(
                    "customerName", order.getEmail(),
                    "orderId", order.getOrderDTO().getOrderId(),
                    "orderDate", order.getOrderDTO().getCreatedAt().toString(),
                    "orderItems", orderItemsHtml,
                    "grandTotal", formattedGrandTotal,
                    "actionUrl", "https://yourapp.com/orders/" + order.getOrderDTO().getOrderId()
            );

            // Replace placeholders with actual values
            String htmlContent = replacePlaceholders(template, variables);

            // Create a MimeMessage
            MimeMessage message = mailSender.createMimeMessage();

            // Use MimeMessageHelper to set email properties
            MimeMessageHelper helper = new MimeMessageHelper(message, true, "UTF-8");
            helper.setTo(order.getEmail());
            helper.setSubject("Your Order Confirmation - " + order.getOrderDTO().getOrderId());
            helper.setText(htmlContent, true); // true indicates HTML

            // (Optional) Set the sender's email address
            // helper.setFrom("your_email@gmail.com");

            // Send the email
            mailSender.send(message);
            logger.info("Order confirmation email sent to {}", order.getEmail());

        } catch (Exception e) {
            logger.error("Failed to send order confirmation email for Order ID {}: {}", order.getOrderDTO().getOrderId(), e.getMessage());
            throw e;
        }
    }

    /**
     * Loads an HTML template from the classpath.
     *
     * @param path Path to the template file
     * @return Template content as a String
     * @throws IOException if reading fails
     */
    private String loadTemplate(String path) throws IOException {
        ClassPathResource resource = new ClassPathResource(path);
        StringBuilder contentBuilder = new StringBuilder();

        try (BufferedReader reader = new BufferedReader(
                new InputStreamReader(resource.getInputStream(), StandardCharsets.UTF_8))) {
            String line;
            while((line = reader.readLine()) != null){
                contentBuilder.append(line).append("\n");
            }
        }

        return contentBuilder.toString();
    }

    /**
     * Replaces placeholders in the template with actual values.
     *
     * @param template The email template with placeholders
     * @param variables Map of placeholders and their corresponding values
     * @return The final email content
     */
    private String replacePlaceholders(String template, Map<String, String> variables){
        String result = template;
        for(Map.Entry<String, String> entry : variables.entrySet()){
            String placeholder = "{" + entry.getKey() + "}";
            result = result.replace(placeholder, entry.getValue());
        }
        return result;
    }
}


// Node: repos/cloned_ms_repos/springboot-kafka-microservices/email-service/src/main/java/net/javaguides/email_service/service/EmailService.java:EmailService.InputStreamReader
