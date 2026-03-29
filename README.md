# 🛒 Ứng dụng luật kết hợp trong Phân tích Giỏ hàng Bán lẻ

Dự án này là một ứng dụng hỗ trợ phân tích dữ liệu giỏ hàng bán lẻ, sử dụng thuật toán FP-Growth để tìm ra các quy luật mua sắm của khách hàng. Mục tiêu là giúp chủ cửa hàng đưa ra quyết định tốt hơn trong việc sắp xếp hàng hóa và tạo các chương trình khuyến mãi chéo (mua sản phẩm này gợi ý thêm sản phẩm khác).

---

## 📌 1. Các Tính Năng Cốt Lõi

Hệ thống cung cấp hai luồng phân tích chính dựa trên dữ liệu giao dịch:

*   **🏪 Luồng 1 - Gợi ý Xếp Kệ Hàng (Gom nhóm theo Danh mục phụ / Subcategory)**
    *   Thuật toán quét qua các giỏ hàng để tìm các nhóm danh mục phụ thường được khách hàng mua cùng nhau nhất.
    *   Hệ thống dùng chỉ số Lift (mức độ tương quan thực tế) > 1.2 để đảm bảo các danh mục này thực sự có liên kết tự nhiên chứ không phải ngẫu nhiên.
    *   *Ứng dụng:* Giúp cửa hàng biết nên đặt các kệ hàng nào gần nhau để tăng doanh số dắt dây.

*   **🎁 Luồng 2 - Gợi ý Combo Chéo (Gom nhóm theo Tên sản phẩm / Product Name)**
    *   Đầu tiên, hệ thống sẽ lọc ra các "sản phẩm ế" - là những món hàng bán rất chậm (thuộc nhóm 15% thấp nhất) nhưng lại có biên lợi nhuận cao (từ 40% trở lên).
    *   Sau đó, hệ thống tìm kiếm những sản phẩm bán chạy (hot) thường xuất hiện chung trong giỏ hàng với các món ế này.
    *   *Ứng dụng:* Giúp cửa hàng đóng gói combo: Mua sản phẩm Hot tặng kèm/giảm giá sản phẩm ế để đẩy hàng tồn kho cục bộ mà vẫn thu về mức lợi nhuận tốt.

---

## 📂 2. Cấu Trúc Mã Nguồn

1.  **`app.py`**: Giao diện chính trên web được xây dựng bằng Streamlit. Tại đây, bạn có thể tải lên file dữ liệu (`.csv`) và điều chỉnh các thanh kéo (slider) như mức Min Support (số nhóm/giỏ hàng tối thiểu) hay Min Confidence (độ tin cậy) để xem kết quả Gợi ý xếp kệ và Gợi ý combo thay đổi trực quan.
2.  **`FP_growth.py`**: Chứa mã nguồn cài đặt thuật toán FP-Growth tự viết (không dùng thư viện có sẵn). File này làm nhiệm vụ chính yếu là dựng cây FP-Tree và rút trích ra các luật kết hợp.
3.  **`BTL.py`**: Phiên bản chạy thẳng thuật toán qua dòng lệnh (console). Giúp lập trình viên in ra các log chi tiết của từng bước chạy thuật toán để dễ dàng gỡ lỗi hoặc kiểm thử trước khi ráp lên web.
4.  **`visualize_data.py`**: Chứa các đoạn mã vẽ biểu đồ bằng Pandas và Seaborn. Dùng để sinh ra các biểu đồ thống kê mô tả tình trạng các nhóm hàng bán chậm từ dữ liệu đầu vào.
5.  **Dữ liệu mẫu**: Gồm cặp tập tin mẫu định dạng `csv` (ví dụ: `sales_*.csv` và `products_*.csv`) dùng làm đầu vào minh họa cho phân tích.

---

## 🚀 3. Hướng Dẫn Vận Hành

Bạn cần cài đặt sẵn Python trên máy tính của mình (khuyên dùng Python phiên bản 3.9 trở lên).

### Bước 1: Cài đặt thư viện yêu cầu
Mở Terminal / Command Prompt ngay tại thư mục chứa dự án này và thi hành lệnh sau để tải về các gói tiện ích dùng cho phân tích (`pandas`, `matplotlib`, `seaborn`, `streamlit`):

```bash
pip install -r requirements.txt
```

### Bước 2: Xem các biểu đồ tổng quan (Dành cho người phân tích số liệu)
Nếu bạn muốn theo dõi đồ thị hiện trạng các mặt hàng tồn kho, hãy gõ:
```bash
python visualize_data.py
```
*(Lưu ý: Nếu một biểu đồ hiện ra, bạn cần tắt khung cửa sổ của biểu đồ đó đi thì chương trình mới chạy tiếp để hiển thị biểu đồ tiếp theo).*

### Bước 3: Chạy giao diện Website Phân tích Nội bộ
Để kích hoạt ứng dụng giao diện web trực tiếp trên máy của bạn, hãy chạy lệnh:
```bash
streamlit run app.py
```

Một tab mới trên trình duyệt sẽ tự động mở lên. Căn cứ theo đó, bạn có thể tự mình điều chỉnh các khoảng tham số bên thanh cấu hình (sidebar) để nhận Gợi ý phân bổ kệ hàng mới nhất.
