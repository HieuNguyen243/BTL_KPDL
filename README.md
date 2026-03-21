# 🛒 Ứng dụng AI Phân tích Giỏ hàng Bán lẻ (Market Basket Analysis)

Dự án này là một hệ thống khai phá dữ liệu (Data Mining) ứng dụng giải thuật học máy Association Rules (**FP-Growth**) để phân tích hành vi mua sắm trong thương mại điện tử/siêu thị bán lẻ. Hệ thống đã được số hóa hoàn toàn từ các thuật toán phức tạp thành một nền tảng Web App tương tác mượt mà, sẵn sàng phục vụ cho các nhà Quản lý Chiến lược (Business Manager / Sales).

---

## 📌 1. Các Tính Năng Cốt Lõi (Core Features)

Hệ thống tập trung bóc tách Dữ liệu Giao dịch theo 2 "Điểm mù" của giới phân tích thị trường:

*   **🏪 Luồng 1 - Tối ưu Không Gian Kệ Hàng (Natural Layout)**
    *   Tự động phát hiện các tập sản phẩm BỔ TRỢ MUA CHUNG với tần suất cực kỳ tự nhiên. Mức Lift nội bộ cấu hình khắt khe `> 1.2` (Chắc chắn hơn mua rời).
    *   *Ứng dụng:* Đặt hàng hóa lên gần nhau trên kệ siêu thị hoặc hệ thống AI Recommendation "Gợi ý mua cùng".

*   **🎁 Luồng 2 - Thiết Kế Combo Giải Cứu Hàng Chậm Luân Chuyển**
    *   Truy lùng tận gốc những ngách sản phẩm có **Lãi Rất Lớn (>= 40%)** nhưng lọt lưới thảm họa **Tốc độ bán cực thấp (Bottom 15%)**.
    *   Ép máy học (Machine) đẩy `Min Confidence` về sát đáy mốc `0.001` - ép nó tìm ra những điểm neo nối Sản phẩm Hot (Hàng Tốt) sang Sản phẩm Ế (Hàng Mục Tiêu).
    *   *Ứng dụng:* Làm chương trình khuyến mãi mua Hàng Đầu Kéo - Tặng kèm thẻ giảm giá mua Hàng Kẹt Kho! Đẩy doanh thu Lãi Lớn lên nhanh nhất có thể.

---

## 📂 2. Cấu Trúc Mã Nguồn (Architecture)

1.  **`app.py`**: Trái tim của ứng dụng. Phần mềm giao diện dựng bằng **Streamlit** mạnh mẽ, xử lý State Management siêu ưu việt. Cho phép người dùng trực tiếp tinh chỉnh *Min Support*, *Min Confidence*, *Upfile CSV* và Search luật sinh.
2.  **`FP_growth.py`**: Lõi não bộ. Được thiết kế thủ công toàn bộ bằng OOP (Không dùng thư viện mì ăn liền). Xây dựng một luồng kiến trúc Cây *Frequent Pattern Tree*, duyệt sâu tìm Luật.
3.  **`visualize_data.py`**: Trình Khám phá số liệu (Data Insight Visualization) bằng Pandas / Seaborn. Vẽ ra các mảng *Nghịch lý Thanh Khoản*, *Sparsity (Khoảng Trống Ma Trận)* phân tích nguyên nhân tại sao máy học gặp khó khăn với bài toán bán lẻ.
4.  **`BTL.py`**: Bản mô phỏng dòng lệnh (Console). Tốc độ cao nhưng phục vụ cho Kỹ sư phân tích thuật toán đằng sau.
5.  **`sales.csv` & `products.csv`**: Bộ dữ liệu mẫu bắt buộc cho hệ thống.

---

## 🚀 3. Hướng Dẫn Vận Hành (How to run)

Đảm bảo máy của bạn đã cài đặt Python 3.9 trở lên.

### Bước 1: Cài đặt thư viện môi trường ngầm
Mở Terminal ở thư mục dự án này, gõ lệnh cài đặt mọi tiện ích liên quan. Hệ thống khai phá dùng `pandas`,`matplotlib`,`seaborn`, và `streamlit`:

```bash
pip install -r requirements.txt
```

### Bước 2: Khám Phá Data (Dành cho Data Analyst) - *Tùy chọn*
Xem các Chart trực quan giải thích sự phân cực của Hàng Ế (Long tail phenomenon) và Không gian Hố Đen bằng mã:
```bash
python visualize_data.py
```
*(Lưu ý: Bạn phải đóng cửa sổ hiển thị Chart n-1 thì Chart n mới phóng lên)*.

### Bước 3: Truy cập trang web tại đường link

https://khaiphadulieu-nhom4.streamlit.app/


---

💡 **Project được rèn tạo dành riêng cho Bài Toán Quản Lý Hiệu Năng Bán Lẻ.**
